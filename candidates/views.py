from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ResumeUploadForm, CandidateSignUpForm
from .models import CandidateProfile
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


@login_required
def candidate_dashboard(request):
    candidate_profile, created = CandidateProfile.objects.get_or_create(
        user=request.user)
    if request.method == 'POST':
        form = ResumeUploadForm(
            request.POST, request.FILES, instance=candidate_profile)
        if form.is_valid():
            form.save()
            return redirect('candidate_dashboard')
    else:
        form = ResumeUploadForm(instance=candidate_profile)
    return render(request, 'candidates/dashboard.html', {'form': form, 'candidate_profile': candidate_profile})


class CandidateLoginView(LoginView):
    template_name = 'candidates/login.html'

    def get_success_url(self):
        # Ensures redirection to dashboard
        return reverse_lazy('candidate_dashboard')


def candidate_signup(request):
    if request.method == 'POST':
        form = CandidateSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a CandidateProfile for the new user
            CandidateProfile.objects.create(user=user)
            # Log the user in after sign-up (optional)
            from django.contrib.auth import login
            login(request, user)
            return redirect('candidate_dashboard')
    else:
        form = CandidateSignUpForm()
    return render(request, 'candidates/signup.html', {'form': form})
