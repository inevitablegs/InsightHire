from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from candidates.models import CandidateProfile
from django.contrib.auth.views import LoginView
from .forms import InterviewerSignUpForm
from django.urls import reverse_lazy
from .utils import generate_interview_questions, schedule_meeting, transcribe_audio
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
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

@login_required
def interviewer_dashboard(request):
    resumes = CandidateProfile.objects.exclude(resume__isnull=True).exclude(resume__exact='')
    questions = None
    meeting_link = None
    evaluation_reports = {}

    interviewer_profile, created = InterviewerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        resume_id = request.POST.get('resume_id')
        candidate = CandidateProfile.objects.get(id=resume_id)

        if 'generate_questions' in request.POST:
            questions = generate_interview_questions(candidate.resume.path)

        elif 'schedule_meeting' in request.POST:
            start_time = request.POST.get('start_time')

            new_meeting_link = schedule_meeting(
                topic=f"Interview with {candidate.user.username}",
                start_time=start_time,
                zoom_account_id=interviewer_profile.zoom_account_id,
                zoom_client_id=interviewer_profile.zoom_client_id,
                zoom_client_secret=interviewer_profile.zoom_client_secret
            )

            if new_meeting_link:
                candidate.meeting_link = new_meeting_link
                candidate.save()
                meeting_link = new_meeting_link

        elif 'process_audio' in request.POST and 'audio_file' in request.FILES:
            audio_file = request.FILES['audio_file']

            # ✅ Save the uploaded file temporarily
            audio_path = f"media/uploads/{audio_file.name}"
            path = default_storage.save(audio_path, ContentFile(audio_file.read()))

            # ✅ Transcribe the audio using the saved file path
            evaluation_reports[resume_id] = transcribe_audio(default_storage.path(path))

            # ✅ Optionally, delete the file after processing (uncomment to enable cleanup)
            # default_storage.delete(path)

    return render(request, 'interviewers/dashboard.html', {
        'resumes': resumes,
        'questions': questions,
        'meeting_link': meeting_link,
        'evaluation_reports': evaluation_reports
    })
