from ninja import Router
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken, AccessToken
from .models import UserProfile, Country
from .schemas import (
    RegisterSchema,
    LoginSchema,
    TokenResponseSchema,
    UserSchema,
    RefreshTokenSchema,
    MessageSchema,
    UserProfileSchema,
    UserProfileUpdateSchema,
    CountriesListSchema,
    CountryOptionSchema,
)

User = get_user_model()
router = Router(tags=["authentication"])


@router.post(
    "/register",
    response={201: TokenResponseSchema, 400: MessageSchema},
    summary="Register a new user",
    description="Create a new user account and return JWT tokens"
)
def register(request, payload: RegisterSchema):
    """
    Register a new user.
    
    Creates a new user account and returns JWT access and refresh tokens.
    """
    # Check if username already exists
    if User.objects.filter(username=payload.username).exists():
        raise HttpError(400, "Username already exists")
    
    # Check if email already exists
    if User.objects.filter(email=payload.email).exists():
        raise HttpError(400, "Email already exists")
    
    # Check if passwords match
    if payload.password != payload.password_confirm:
        raise HttpError(400, "Passwords do not match")
    
    # Validate password
    try:
        validate_password(payload.password, user=User(username=payload.username))
    except ValidationError as e:
        raise HttpError(400, f"Password validation failed: {', '.join(e.messages)}")
    
    # Create user
    user = User.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name or '',
        last_name=payload.last_name or '',
    )
    
    # Generate tokens
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    
    return 201, TokenResponseSchema(
        access=str(access),
        refresh=str(refresh),
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    )


@router.post(
    "/login",
    response={200: TokenResponseSchema, 401: MessageSchema},
    summary="Login user",
    description="Authenticate user and return JWT tokens"
)
def login(request, payload: LoginSchema):
    """
    Login user.
    
    Authenticates the user with username and password, returns JWT tokens.
    """
    user = authenticate(
        request,
        username=payload.username,
        password=payload.password
    )
    
    if user is None:
        raise HttpError(401, "Invalid username or password")
    
    if not user.is_active:
        raise HttpError(401, "User account is disabled")
    
    # Generate tokens
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    
    return TokenResponseSchema(
        access=str(access),
        refresh=str(refresh),
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    )


@router.post(
    "/refresh",
    response={200: TokenResponseSchema, 401: MessageSchema},
    summary="Refresh access token",
    description="Get a new access token using a refresh token"
)
def refresh_token(request, payload: RefreshTokenSchema):
    """
    Refresh access token.
    
    Returns a new access token using a valid refresh token.
    """
    try:
        refresh_token = RefreshToken(payload.refresh)
        user = refresh_token.user
        
        # Generate new tokens
        new_refresh = RefreshToken.for_user(user)
        new_access = new_refresh.access_token
        
        return TokenResponseSchema(
            access=str(new_access),
            refresh=str(new_refresh),
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        )
    except Exception as e:
        raise HttpError(401, "Invalid or expired refresh token")


@router.get(
    "/me",
    response=UserSchema,
    auth=JWTAuth(),
    summary="Get current user",
    description="Get information about the currently authenticated user"
)
def get_current_user(request):
    """
    Get current user.
    
    Returns information about the currently authenticated user.
    Requires a valid JWT token.
    """
    return request.auth


@router.post(
    "/logout",
    response={200: MessageSchema},
    auth=JWTAuth(),
    summary="Logout user",
    description="Invalidate the current refresh token (if using token blacklist)"
)
def logout(request, payload: RefreshTokenSchema):
    """
    Logout user.
    
    Invalidates the refresh token. Note: This requires token blacklist to be enabled.
    """
    try:
        refresh_token = RefreshToken(payload.refresh)
        refresh_token.blacklist()
        return MessageSchema(message="Successfully logged out")
    except Exception as e:
        raise HttpError(400, "Invalid refresh token")


@router.get(
    "/profile",
    response=UserProfileSchema,
    auth=JWTAuth(),
    summary="Get user profile",
    description="Get the current user's profile information"
)
def get_user_profile(request):
    """
    Get user profile.
    
    Returns the complete profile information for the authenticated user.
    """
    user = request.auth
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Get country display name
    country_display = None
    if profile.country:
        country_display = dict(Country.choices).get(profile.country)
    
    return UserProfileSchema(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=profile.phone_number,
        street=profile.street,
        city=profile.city,
        postcode=profile.postcode,
        country=profile.country,
        country_display=country_display,
        date_joined=user.date_joined.isoformat(),
        created_at=profile.created_at.isoformat() if profile.created_at else None,
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None,
    )


@router.put(
    "/profile",
    response=UserProfileSchema,
    auth=JWTAuth(),
    summary="Update user profile",
    description="Update the current user's profile information"
)
def update_user_profile(request, payload: UserProfileUpdateSchema):
    """
    Update user profile.
    
    Updates the profile information for the authenticated user.
    Only provided fields will be updated.
    """
    user = request.auth
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Update user fields
    if payload.email is not None:
        # Check if email is already taken by another user
        if User.objects.filter(email=payload.email).exclude(id=user.id).exists():
            raise HttpError(400, "Email address is already in use")
        user.email = payload.email
    
    if payload.first_name is not None:
        user.first_name = payload.first_name
    
    if payload.last_name is not None:
        user.last_name = payload.last_name
    
    user.save()
    
    # Update profile fields
    if payload.phone_number is not None:
        profile.phone_number = payload.phone_number
    
    if payload.street is not None:
        profile.street = payload.street
    
    if payload.city is not None:
        profile.city = payload.city
    
    if payload.postcode is not None:
        profile.postcode = payload.postcode
    
    if payload.country is not None:
        # Validate country code
        valid_countries = [code for code, _ in Country.choices]
        if payload.country not in valid_countries:
            raise HttpError(400, f"Invalid country code. Must be one of: {', '.join(valid_countries)}")
        profile.country = payload.country
    
    profile.save()
    
    # Get country display name
    country_display = None
    if profile.country:
        country_display = dict(Country.choices).get(profile.country)
    
    return UserProfileSchema(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=profile.phone_number,
        street=profile.street,
        city=profile.city,
        postcode=profile.postcode,
        country=profile.country,
        country_display=country_display,
        date_joined=user.date_joined.isoformat(),
        created_at=profile.created_at.isoformat() if profile.created_at else None,
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None,
    )



@router.get(
    "/countries",
    response=CountriesListSchema,
    summary="Get available countries",
    description="Get a list of all available countries for user profiles"
)
def get_countries(request):
    """
    Get available countries.
    
    Returns a list of all available countries that can be used in user profiles.
    """
    countries = [
        CountryOptionSchema(code=code, name=name)
        for code, name in Country.choices
    ]
    return CountriesListSchema(countries=countries)
