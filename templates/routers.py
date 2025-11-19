from ninja import Router
from ninja_jwt.authentication import JWTAuth
from ninja.errors import HttpError
from .models import TypstTemplate
from .schemas import (
    TypstTemplateListResponse,
    ConvertToPdfRequest,
    ConvertToPdfResponse,
)
from django.contrib.auth import get_user_model
from authentication.models import Country
from jinja2 import Template
import base64
import typst

User = get_user_model()
router = Router(tags=["templates"])


def escape_typst_characters(text: str) -> str:
    """
    Escape special Typst characters that need a backslash before them.
    Special characters: #, @, <, >, $, \\, _, *
    """
    if not text:
        return text
    
    # Escape backslash first to avoid double-escaping
    text = text.replace('\\', '\\\\')
    
    # Escape other special characters
    special_chars = ['#', '@', '<', '>', '$', '_', '*']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def _render_template_to_pdf(template_code: str, template_vars: dict) -> str:
    """
    Helper function to render Jinja2 template and compile to PDF.
    
    Args:
        template_code: Typst template code with Jinja2 variables
        template_vars: Dictionary of variables to render in the template
        
    Returns:
        str: Base64-encoded PDF
        
    Raises:
        HttpError: If template rendering or PDF compilation fails
    """
    # Render the template with Jinja2
    try:
        jinja_template = Template(template_code)
        rendered_result = jinja_template.render(**template_vars)
    except Exception as e:
        raise HttpError(500, f"Failed to render template: {str(e)}")
    
    # Compile the Typst file to PDF using Python typst library
    try:
        # Compile Typst content directly to PDF bytes
        pdf_bytes = typst.compile(rendered_result.encode('utf-8'))
        
        # Base64 encode the PDF
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        return pdf_base64
        
    except Exception as e:
        raise HttpError(500, f"Failed to compile Typst to PDF: {str(e)}")


@router.get(
    "/",
    response=TypstTemplateListResponse,
    auth=JWTAuth(),
    summary="Get all Typst templates",
    description="Retrieve all Typst templates from the database. Requires authentication."
)
def find_all_templates(request):
    """
    Find all Typst templates.
    
    Returns a list of all templates with their metadata.
    Requires a valid JWT token in the Authorization header.
    """
    templates = TypstTemplate.objects.all()
    templates_list = list(templates)
    
    return TypstTemplateListResponse(
        templates=templates_list,
        count=len(templates_list)
    )


@router.post(
    "/convert-to-pdf",
    response=ConvertToPdfResponse,
    auth=JWTAuth(),
    summary="Convert cover letter text to PDF",
    description="Convert cover letter text to a PDF using a Typst template. Takes the content, company name, and template ID to generate a formatted PDF. Requires authentication."
)
def convert_to_pdf(request, payload: ConvertToPdfRequest):
    """
    Convert cover letter text to PDF using a Typst template.
    
    This endpoint:
    1. Fetches the authenticated user from JWT token
    2. Fetches the template from the database
    3. Applies the template with user data, company name, and content
    4. Compiles to PDF and returns base64-encoded result
    
    Requires a valid JWT token in the Authorization header.
    """
    
    # Get authenticated user from JWT token
    user = request.user
    
    # Ensure user profile exists
    try:
        user = User.objects.select_related('profile').get(id=user.id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")
    
    # Fetch template
    try:
        template = TypstTemplate.objects.get(id=payload.template_id)
    except TypstTemplate.DoesNotExist:
        raise HttpError(404, "Template not found")
    
    # Get user profile data
    profile = user.profile
    
    # Escape Typst special characters in the content
    escaped_content = escape_typst_characters(payload.content)
    
    # Prepare template variables for Jinja2
    template_vars = {
        "company_name": payload.company_name,
        "street": profile.street or "",
        "post_code": profile.postcode or "",
        "city": profile.city or "",
        "country": Country(profile.country).label if profile.country else "",
        "email": escape_typst_characters(user.email),
        "content": escaped_content,
    }
    
    # Render template and compile to PDF using helper function
    pdf_base64 = _render_template_to_pdf(template.code, template_vars)
    
    return ConvertToPdfResponse(
        pdf_base64=pdf_base64,
        success=True
    )
