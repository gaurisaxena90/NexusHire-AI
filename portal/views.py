import PyPDF2
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from .models import UserProfile, JobPost, JobApplication
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'portal/index.html')

@login_required(login_url='login')
def hr_dashboard(request):
    # NAYA CODE: Jab HR naya job form submit kare
    if request.method == 'POST':
        job_title = request.POST.get('title')
        company = request.POST.get('company_name')
        job_location = request.POST.get('location')
        job_salary = request.POST.get('salary')
        job_description = request.POST.get('description')

        # Database mein naya job save karna (hr=request.user zaroori hai taaki usi HR ko dikhe)
        JobPost.objects.create(
            hr=request.user,
            title=job_title,
            company_name=company,
            location=job_location,
            salary=job_salary,
            description=job_description
        )
        
        # Save hone ke baad page ko refresh (redirect) karna taaki data turant update ho jaye
        return redirect('hr_dashboard')

    # --- Niche ka aapka purana code waisa hi rahega ---
    my_jobs = JobPost.objects.filter(hr=request.user).order_by('-created_at')
    applications = JobApplication.objects.filter(job__hr=request.user).order_by('-applied_on')
    
    pending_count = applications.filter(status='Pending Review').count()
    shortlisted_count = applications.filter(status='Shortlisted').count()
    interviewing_count = applications.filter(status='Interviewing').count()
    rejected_count = applications.filter(status='Rejected').count()

    context = {
        'jobs': my_jobs,
        'applications': applications,
        'pending_count': pending_count,
        'shortlisted_count': shortlisted_count,
        'interviewing_count': interviewing_count,
        'rejected_count': rejected_count,
    }
    
    return render(request, 'portal/hr-dashboard.html', context)

@login_required(login_url='login')
def candidate_dashboard(request):
    user = request.user
    
    # 1. Profile Strength Calculation Logic
    profile_strength = 0
    
    if user.first_name or user.last_name:
        profile_strength += 40  # Naam hone par 40%
        
    if user.email:
        profile_strength += 30  # Email hone par 30%

    # 2. Jobs aur Applications ka data nikalna
    jobs = JobPost.objects.all().order_by('-created_at')
    applications = JobApplication.objects.filter(candidate=user).order_by('-applied_on')
    
    # Agar candidate ne kam se kam ek job par apply (resume upload) kiya hai
    if applications.exists():
        profile_strength += 30  # Resume upload hone par bache hue 30% add ho gaye (Total 100%)
        
    # 3. AI Extracted Skills Count nikalna (Dashboard par jo teesra 0 hai uske liye)
    parsed_skills_count = 0
    if applications.exists():
        latest_app = applications.first()
        # Matched aur missing skills ki ginti
        if latest_app.matched_skills:
            parsed_skills_count += len(latest_app.matched_skills)
        if latest_app.missing_skills:
            parsed_skills_count += len(latest_app.missing_skills)

    # 4. Saara data HTML ko bhejna
    context = {
        'jobs': jobs,
        'applications': applications,
        'profile_strength': profile_strength,         # Naya Data
        'parsed_skills_count': parsed_skills_count,   # Naya Data
    }
    return render(request, 'portal/candidate-dashboard.html', context)
def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # User ko verify karna
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            # Role ke hisaab se redirect
            if hasattr(user, 'userprofile'):
                if user.userprofile.role == 'HR':
                    return redirect('hr_dashboard')
                else:
                    return redirect('candidate_dashboard')
        else:
            return render(request, 'portal/login.html', {'error': 'Invalid email or password'})
            
    return render(request, 'portal/login.html')

def register_page(request):
    if request.method == 'POST':
        # Form se data nikalna
        role = request.POST.get('role')
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Check karna ki kya is email se pehle koi user hai
        if not User.objects.filter(username=email).exists():
            # Naya User create karna
            user = User.objects.create_user(username=email, email=email, password=password, first_name=fullname)
            
            # User ka Profile (HR/Candidate) set karna
            UserProfile.objects.create(user=user, role=role)
            
            # Account banne ke baad automatic login karwana
            login(request, user)
            
            # Role ke hisaab se sahi dashboard par bhejna
            if role == 'HR':
                return redirect('hr_dashboard')
            else:
                return redirect('candidate_dashboard')
        else:
            # Agar account pehle se hai toh wapas register page par bhej do
            return render(request, 'portal/register.html', {'error': 'Email already exists!'})

    return render(request, 'portal/register.html')

def logout_user(request):
    logout(request)
    return redirect('login') # Logout hone ke baad wapas login page par bhej dega

def delete_job(request, job_id):
    # Job ko dhoondho
    job = get_object_or_404(JobPost, id=job_id, hr=request.user)
    
    # Job ko database se delete kar do
    job.delete()
    
    # Delete hone ke baad wapas dashboard par bhej do
    return redirect('hr_dashboard')

def edit_job(request, job_id):
    # Puraani job ko database se nikalna
    job = get_object_or_404(JobPost, id=job_id, hr=request.user)
    
    if request.method == 'POST':
        # Form se naya data nikal kar purane data ke upar overwrite karna
        job.title = request.POST.get('title')
        job.company_name = request.POST.get('company_name')
        job.location = request.POST.get('location')
        job.salary = request.POST.get('salary')
        job.description = request.POST.get('description')
        job.save() # Changes ko database mein save kar dena
        
        return redirect('hr_dashboard')
        
    return render(request, 'portal/edit-job.html', {'job': job})

def apply_job(request, job_id):
    if request.method == 'POST':
        job = get_object_or_404(JobPost, id=job_id)
        resume_file = request.FILES.get('resume')
        
        if resume_file:
            try:
                # 1. PEHLE PDF READ KARO (Bina Database mein save kiye)
                resume_file.seek(0)
                pdf_reader = PyPDF2.PdfReader(resume_file)
                extracted_text = ""
                for page in pdf_reader.pages:
                    extracted_text += page.extract_text()
                
                text_lower = extracted_text.lower()
                job_desc_lower = job.description.lower()
                
                score = 40  # Base Score
                
                # Hum in skills ko check karenge (Aapke institute courses ke hisaab se)
                skills_to_check = ['python', 'django', 'html', 'css', 'tally', 'o level', 'ccc', 'adca']
                
                matched = []
                missing = []
                
                # Check karo ki job mein kya maanga hai, aur resume mein kya hai
                for skill in skills_to_check:
                    if skill in job_desc_lower: # Agar job mein ye skill chahiye
                        if skill in text_lower: # Aur resume mein bhi hai
                            score += 15
                            matched.append(skill.title())
                        else: # Agar resume mein nahi hai
                            missing.append(skill.title())
                
                # 2. --- NAYA GATEKEEPER LOGIC (Strict Checking) ---
                # Agar score 50 se kam hai (Yani koi khass skill match nahi hui)
                if score < 50:
                    messages.error(request, "Your CV skills do not match our requirements. Please upload a relevant CV.")
                    return redirect('candidate_dashboard')  # Yahan se wapas bhej diya, save NAHI kiya!
                
                # 3. Agar score achha hai, TABHI application ko database mein save karein
                application = JobApplication.objects.create(
                    job=job,
                    candidate=request.user,
                    resume=resume_file,
                    ai_match_score=min(score, 99),
                    matched_skills=matched,
                    missing_skills=missing,
                    status='Pending Review'
                )
                
                messages.success(request, "Excellent! Your relevant CV has been submitted successfully.")
                
            except Exception as e:
                print("PDF parse error:", e)
                messages.error(request, "There was an error reading your PDF. Please try a different file.")
                
        return redirect('candidate_dashboard') 
        
    return redirect('candidate_dashboard')

@login_required(login_url='login')
def update_status(request, app_id, status):
    if request.method == 'POST':
        # Database से वो एप्लीकेशन निकालो
        application = get_object_or_404(JobApplication, id=app_id)
        
        # स्टेटस अपडेट करो (Shortlisted या Rejected)
        if status in ['Shortlisted', 'Rejected']:
            application.status = status
            application.save()
            
            if status == 'Shortlisted':
                messages.success(request, f"{application.candidate.first_name} has been Shortlisted!")
            else:
                messages.error(request, f"{application.candidate.first_name} has been Rejected.")
                
    return redirect('hr_dashboard')