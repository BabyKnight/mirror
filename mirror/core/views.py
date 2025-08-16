from django.forms.models import model_to_dict
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from .models import Sample, Image, Task, TestCase, Platform, UserProfile
from .utils import get_chart_data, get_sample_trends, get_image_trends, get_task_trends, get_tc_fr_trends
from datetime import datetime, timezone, timedelta
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncDate
from django.views.decorators.csrf import csrf_exempt
import os


def dummy_view(request, *args, **kwargs):
    return JsonResponse({'detail': 'Not implimented yet'}, status=501)


def index(request):

    now = datetime.now(timezone.utc)

    sample_trend = get_sample_trends()
    image_trend = get_image_trends()
    task_trend = get_task_trends()
    fr_trend = get_tc_fr_trends()

    # recent activity
    all_task = Task.objects.order_by('-time_trigger')[:5]
    activity_list = []

    for i in all_task:
        activity = {}
        activity['user'] = i.trigger_by.user.get_full_name()
        activity['detail'] = "Trigger " +   i.get_task_category_display() + " on " + i.sample.dpn +"."

        total_sec = (now - i.time_trigger).total_seconds()
        if total_sec < 3600:
            activity['time'] = str(int(total_sec // 60)) + ' Minutes Ago'
        elif total_sec < 86400:
            activity['time'] = str(int(total_sec // 3600)) + ' Hours Ago'
        else:
            activity['time'] = str(int(total_sec // 86400)) + ' Days Ago'

        activity_list.append(activity)

    context = {
        "trends": [sample_trend, image_trend, task_trend, fr_trend],
        "activity_list": activity_list,
    }
    return render(request, 'index.html', context)


def dashboard(request):
    now = datetime.now(timezone.utc)

    sample_trend = get_sample_trends()
    image_trend = get_image_trends()
    task_trend = get_task_trends()
    fr_trend = get_tc_fr_trends()

    # recent activity
    all_task = Task.objects.order_by('-time_trigger')[:5]
    activity_list = []

    for i in all_task:
        activity = {}
        activity['user'] = i.trigger_by.user.get_full_name()
        activity['detail'] = "Trigger " +   i.get_task_category_display() + " on " + i.sample.dpn +"."

        total_sec = (now - i.time_trigger).total_seconds()
        if total_sec < 3600:
            activity['time'] = str(int(total_sec // 60)) + ' Minutes Ago'
        elif total_sec < 86400:
            activity['time'] = str(int(total_sec // 3600)) + ' Hours Ago'
        else:
            activity['time'] = str(int(total_sec // 86400)) + ' Days Ago'

        activity_list.append(activity)

    context = {
        "trends": [sample_trend, image_trend, task_trend, fr_trend],
        "activity_list": activity_list,
    }
    return render(request, 'dashboard.html', context)


def sample(request):
    samples = Sample.objects.all()
    sample_list = []
    plat_info_list = []
    user_list = []

    for i in samples:
        sp = model_to_dict(i)
        if i.owner:
            sp['owner'] = i.owner.user.get_full_name()
        else:
            sp['owner'] = ""
        if i.current_user:
            sp['current_user'] = i.current_user.user.get_full_name()
        else:
            sp['current_user'] = ""

        if i.status == '00':
            sp['st'] = 'OFF'
        elif i.status == '10':
            sp['st'] = 'AVL'
        elif i.status in ['11', '12', '13']:
            sp['st'] = 'BSY'
        else:
            sp['st'] = 'UNK'
        sp['plat_name'] = i.platform.name
        sample_list.append(sp)

    platforms = Platform.objects.all()

    for i in platforms:
        plat_info_list.append({
            'id': i.pk,
            'plat_name': i.name,
            })

    users = UserProfile.objects.all()

    build_phase_choices = Sample._meta.get_field('build_phase')
    bp_choices = build_phase_choices.choices

    for i in users:
        user_list.append({
            'id': i.user.id,
            'user_name': i.full_name,
            })

    context = {
        "sample_list": sample_list,
        "platform_list": plat_info_list,
        "user_list": user_list,
        "build_phase": bp_choices,
        }

    return render(request, 'sample.html', context)


def image(request):
    # search for Images
    images = Image.objects.all()
    img_list = []

    for i in images:
        img = model_to_dict(i)
        img['release_date'] = i.release_date.strftime("%Y-%m-%d")
        img['kernel_main_version'] = i.kernel_version.split("-")[0]
        img['kernel_build_version'] = i.kernel_version.split("-")[1]
        img_list.append(img)

    context = {
        "image_list": img_list
        }

    return render(request, 'image.html', context)


def task(request):
    task_list = []
    sample_list = []
    user_list = []
    testcase_list = []
    image_list = []

    now = datetime.now(timezone.utc)

    all_task = Task.objects.all()
    for i in all_task:
        tsk = model_to_dict(i)
        tsk['type'] = i.task_category[0]
        tsk['platform_name'] = i.sample.platform.name
        tsk['dpn'] = i.sample.dpn
        tsk['image_cat'] = i.image.category if i.image else 'Unkonwn'
        tsk['kernel_ver'] = i.image.kernel_version.split('-')[-1] if i.image else 'Unkonwn'
        tsk['trigger_by'] = i.trigger_by.user.get_full_name()
        tsk['st'] = i.status[0]
        total_sec = (now - i.time_trigger).total_seconds()
        if total_sec < 3600:
            tsk['trigger_at'] = str(int(total_sec // 60)) + ' Minutes Ago'
        elif total_sec < 86400:
            tsk['trigger_at'] = str(int(total_sec // 3600)) + ' Hours Ago'
        else:
            tsk['trigger_at'] = str(int(total_sec // 86400)) + ' Days Ago'

        task_list.append(tsk)

    samples = Sample.objects.all()
    for i in samples:
        sample_list.append({
            'id': i.pk,
            'name': i.dpn,
            })

    users = UserProfile.objects.all()
    for i in users:
        user_list.append({
            'id': i.user.id,
            'name': i.full_name,
            })

    images = Image.objects.all()
    for i in images:
        image_list.append({
            'id': i.pk,
            'name': i.image_name,
            })

    testcases = TestCase.objects.all()
    for i in testcases:
        testcase_list.append({
            'id': i.pk,
            'name': i.case_name,
            })

    context = {
        "task_list": task_list,
        'samples': sample_list,
        'users':  user_list,
        'testcases': testcase_list,
        'images': image_list,
        }

    return render(request, 'task.html', context)


def testcase(request):
    tc = TestCase.objects.all()
    tc_list = []

    for i in tc:
        tc_list.append(model_to_dict(i))

    context = {
        "testcase_list": tc_list,
        }

    return render(request, 'test_case.html', context)


def platform(request):
    template_name = f"platform.html"
    html = render_to_string(template_name)
    return HttpResponse(html)





