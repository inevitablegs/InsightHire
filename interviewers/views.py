from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from candidates.models import CandidateProfile
from django.contrib.auth.views import LoginView
from .forms import InterviewerSignUpForm
from django.urls import reverse_lazy
from .utils import generate_interview_questions  # Import the utility function
from .utils import schedule_meeting  # Utility function for Zoom API
from .models import InterviewerProfile

class InterviewerLoginView(LoginView):
    template_name = 'interviewers/login.html'

    def get_success_url(self):
        return reverse_lazy('interviewer_dashboard')

def interviewer_signup(request):
    if request.method == 'POST':
        form = InterviewerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            from django.contrib.auth import login
            login(request, user)

            # ✅ Save InterviewerProfile with Zoom credentials
            InterviewerProfile.objects.create(
                user=user,
                zoom_account_id=form.cleaned_data['zoom_account_id'],
                zoom_client_id=form.cleaned_data['zoom_client_id'],
                zoom_client_secret=form.cleaned_data['zoom_client_secret']
            )

            return redirect('interviewer_dashboard')
    else:
        form = InterviewerSignUpForm()
    return render(request, 'interviewers/signup.html', {'form': form})


@login_required
def interviewer_dashboard(request):
    resumes = CandidateProfile.objects.exclude(resume__isnull=True).exclude(resume__exact='')
    questions = None
    meeting_link = None

    # Get the interviewer's profile
    interviewer_profile, created = InterviewerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if 'generate_questions' in request.POST:
            resume_id = request.POST.get('resume_id')
            resume = CandidateProfile.objects.get(id=resume_id)
            questions = generate_interview_questions(resume.resume.path)

        elif 'schedule_meeting' in request.POST:
            resume_id = request.POST.get('resume_id')
            candidate = CandidateProfile.objects.get(id=resume_id)
            start_time = request.POST.get('start_time')

            # Schedule the meeting and replace old meeting link
            new_meeting_link = schedule_meeting(
                topic=f"Interview with {candidate.user.username}",
                start_time=start_time,
                zoom_account_id=interviewer_profile.zoom_account_id,
                zoom_client_id=interviewer_profile.zoom_client_id,
                zoom_client_secret=interviewer_profile.zoom_client_secret
            )

            if new_meeting_link:
                # ✅ Update candidate's meeting link (overwrite old one)
                candidate.meeting_link = new_meeting_link
                candidate.save()

                # ✅ Update meeting_link variable to display on dashboard
                meeting_link = new_meeting_link

    return render(request, 'interviewers/dashboard.html', {
        'resumes': resumes,
        'questions': questions,
        'meeting_link': meeting_link
    })
