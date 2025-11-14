from ninja import Router
from ninja_jwt.authentication import JWTAuth
from .models import TypstTemplate
from .schemas import TypstTemplateListResponse

router = Router(tags=["templates"])


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

