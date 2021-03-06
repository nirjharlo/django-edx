from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Choice, Question, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging

from django.http import HttpResponse

from inspect import getmembers
from pprint import pprint


# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'

    def get_context_data(self, **kwargs):
        context = super(CourseDetailView, self).get_context_data(**kwargs)
        #context['course'] = Course.objects.all()
        context['choice'] = Choice.objects.all()
        return context



def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
# you may implement it based on following logic:
         # Get user and course object, then get the associated enrollment object created when the user enrolled the course
         # Create a submission object referring to the enrollment
         # Collect the selected choices from exam form
         # Add each selected choice object to the submission object
         # Redirect to show_exam_result with the submission id
#def submit(request, course_id):
def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrollment = Enrollment.objects.get(user=request.user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)

    choices = []
    choice_str = 'choice_'
    for item in dict(request.POST.items()).keys():
        if choice_str in item:
            choice = int(item[7:])
            choice = get_object_or_404(Choice, pk=choice)
            submission.choices.add(choice)

    return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course.id, submission.id)))


# <HINT> A example method to collect the selected choices from the exam form from the request object
#def extract_answers(request):
#    submitted_anwsers = []
#    for key in request.POST:
#        if key.startswith('choice'):
#            value = request.POST[key]
#            choice_id = int(value)
#            submitted_anwsers.append(choice_id)
#    return submitted_anwsers


# <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
# you may implement it based on the following logic:
        # Get course and submission based on their ids
        # Get the selected choice ids from the submission record
        # For each selected choice, check if it is a correct answer or not
        # Calculate the total score
#def show_exam_result(request, course_id, submission_id):
def show_exam_result(request, course_id, submission_id):
    correct_grade = 0

    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    choices_all = Choice.objects.all()
    choices = submission.choices.all()

    total_grade = 0
    total_correct_answers_dict = dict()
    questions = Question.objects.filter(course=course)
    for question in questions:
        total_correct_answers_dict[question.id] = []
        total_grade = total_grade + question.grade
        for choice in choices_all:
            if question in choice.questions.all():
                if choice.is_correct == 1:
                    total_correct_answers_dict[question.id].append(choice.id)


    correct_answers = list()
    correct_grade_dict = dict()
    correct_answers_dict = dict()
    for question_alt in questions:
        correct_answers_dict[question_alt.id] = []
        for choice in choices:
            if question_alt in choice.questions.all():
                if choice.is_correct == 1:
                    correct_answers.append(choice)
                    correct_grade_dict[question_alt.id] = question.grade
                    correct_answers_dict[question_alt.id].append(choice.id)

    for q, ans in total_correct_answers_dict.items():
        if len(correct_answers_dict[q]) != len(ans):
            correct_grade_dict[q] = 0


    correct_grade = sum(correct_grade_dict.values())
    grade = round(( (correct_grade/total_grade) * 100 ), 2)

    context = {}
    context['grade'] = grade
    context['course_id'] = course_id
    context['correct_grade'] = correct_grade
    context['total_grade'] = total_grade
    context['questions'] = questions
    context['choices'] = choices_all
    context['correct_answers'] = correct_answers
    context['correct_grade_dict'] = correct_grade_dict
    context['correct_answers_dict'] = correct_answers_dict
    context['total_correct_answers_dict'] = total_correct_answers_dict
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
