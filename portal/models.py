from django.db import models
from django.contrib.auth.models import User

# 1. User Profile (HR aur Candidate mein difference karne ke liye)
class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('HR', 'HR'),
        ('Candidate', 'Candidate'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    company_name = models.CharField(max_length=100, blank=True, null=True) # Sirf HR ke liye kaam aayega
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

# 2. Job Posting Model
class Job(models.Model):
    hr = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=100, default='Remote')
    experience = models.CharField(max_length=50)
    description = models.TextField()
    skills_required = models.CharField(max_length=255, help_text="Comma se alag karke skills likhein (e.g. Python, Django, AWS)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# 3. Application & Resume Model
class Application(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending Review'),
        ('Shortlisted', 'Shortlisted'),
        ('Rejected', 'Rejected'),
    )
    candidate = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/')
    extracted_skills = models.TextField(blank=True, null=True) # AI jo skills padhega wo yahan aayengi
    ai_match_score = models.IntegerField(default=0) # Match percentage (0-100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.username} applied for {self.job.title}"
    
class JobPost(models.Model):
    # Kis HR ne ye job post ki hai (User model se link)
    hr = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Job ki details
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    salary = models.CharField(max_length=100, blank=True, null=True)
    
    # Job kab post hui uski date aur time automatically save ho jayega
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class JobApplication(models.Model):
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    candidate = models.ForeignKey(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/')
    ai_match_score = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='Pending Review')
    applied_on = models.DateTimeField(auto_now_add=True)
    
    # --- NAYE FIELDS ---
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)

    def __str__(self):
        return f"{self.candidate.username} applied for {self.job.title}"
