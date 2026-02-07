from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string

from .models import ChatSession, ChatMessage
from .services.cashie_service import CashieService


@login_required
def chat_view(request, session_id=None):
    """Main chat page - loads existing session or creates new one."""
    service = CashieService(request.user)

    # Get or create session
    if session_id:
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    else:
        # Get most recent active session or create new
        session = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if not session:
            session = ChatSession.objects.create(user=request.user)

    # Get all user's sessions for sidebar
    sessions = ChatSession.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-updated_at')[:20]

    # Get messages for current session
    messages = session.messages.order_by('created_at')

    # Get welcome suggestions if no messages
    welcome_suggestions = []
    if not messages.exists():
        welcome_suggestions = service.get_welcome_suggestions()

    context = {
        'session': session,
        'sessions': sessions,
        'messages': messages,
        'welcome_suggestions': welcome_suggestions,
    }

    return render(request, 'cashie/chat.html', context)


@login_required
def new_session(request):
    """Create a new chat session and redirect to it."""
    session = ChatSession.objects.create(user=request.user)
    return redirect('cashie:session', session_id=session.id)


@login_required
def send_message(request):
    """Handle sending a message via HTMX POST."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    message_text = request.POST.get('message', '').strip()
    session_id = request.POST.get('session_id')

    if not message_text:
        return HttpResponse(status=400)

    service = CashieService(request.user)

    # Get or create session
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            session = ChatSession.objects.create(user=request.user)
    else:
        session = ChatSession.objects.create(user=request.user)

    # Get the user message we're about to create
    user_message = ChatMessage(
        session=session,
        role=ChatMessage.Role.USER,
        content=message_text
    )

    # Send message and get response
    assistant_message = service.send_message(session, message_text)

    # Fetch the saved user message (created by service)
    user_message = session.messages.filter(role=ChatMessage.Role.USER).order_by('-created_at').first()

    # Render the message pair partial
    html = render_to_string('cashie/partials/_message_pair.html', {
        'user_message': user_message,
        'assistant_message': assistant_message,
    }, request=request)

    response = HttpResponse(html)

    # Add HX-Trigger for updating session title if needed
    if session.messages.count() == 2:
        response['HX-Trigger'] = 'sessionUpdated'

    return response
