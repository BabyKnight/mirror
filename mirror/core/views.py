from django.forms.models import model_to_dict
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from .models import Sample, Image, Task, TestCase, Platform, UserProfile
from .utils import get_chart_data
from datetime import datetime, timezone, timedelta
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncDate
from django.views.decorators.csrf import csrf_exempt
import os


def dummy_view(request, *args, **kwargs):
    return JsonResponse({'detail': 'Not implimented yet'}, status=501)


def index(request):

    now = datetime.now(timezone.utc)

    # total samples by month
    start_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_last_month = (start_of_this_month - timedelta(days=1)).replace(day=1)

    total_sample_this_month = Sample.objects.filter(
                time_created__gte=start_of_this_month,
                time_created__lt=now
            ).count()

    total_sample_last_month = Sample.objects.filter(
                time_created__gte=start_of_last_month,
                time_created__lt=start_of_this_month
            ).count()
    total_sample_delta = total_sample_this_month - total_sample_last_month
    sample_trend = {
                'title': 'Total Sample',
                'data': total_sample_this_month,
                'delta': total_sample_delta,
                'moment': 'Since last month',
            }

    # total image by week
    start_of_week = now - timedelta(days=now.weekday())
    start_of_this_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    start_of_last_week = start_of_this_week - timedelta(days=7)
    end_of_last_week = start_of_this_week - timedelta(seconds=1)

    total_image_this_week = Image.objects.filter(
                release_date__gte=start_of_this_week,
                release_date__lt=now
            ).count()

    total_image_last_week = Image.objects.filter(
                release_date__gte=start_of_last_week,
                release_date__lt=end_of_last_week
            ).count()
    total_image_delta = total_image_this_week - total_image_last_week
    image_trend = {
                'title': 'Image Release',
                'data': total_image_this_week,
                'delta': total_image_delta,
                'moment': 'Since last week',
            }

    # total tasks by month
    total_task_this_month = Task.objects.filter(
                time_trigger__gte=start_of_this_month,
                time_trigger__lt=now
            ).count()

    total_task_last_month = Task.objects.filter(
                time_trigger__gte=start_of_last_month,
                time_trigger__lt=start_of_this_month
            ).count()
    total_task_delta = total_task_this_month - total_task_last_month
    task_trend = {
                'title': 'Total Task',
                'data': total_task_this_month,
                'delta': total_task_delta,
                'moment': 'Since last month'
            }

    # task failure rate by week
    total_failed_task_this_month = Task.objects.filter(
                result=False,
                time_trigger__gte=start_of_this_month,
                time_trigger__lt=now
            ).count()

    total_failed_task_last_month = Task.objects.filter(
                result=False,
                time_trigger__gte=start_of_last_month,
                time_trigger__lt=start_of_this_month
            ).count()
    if total_task_last_month == 0:
        failure_rate_last_month = 0
    else:
        failure_rate_last_month = total_failed_task_last_month / total_task_last_month

    if total_task_this_month == 0:
        failure_rate_this_month = 0
    else:
        failure_rate_this_month = total_failed_task_this_month / total_task_this_month
    failure_rate_delta = round((failure_rate_this_month - failure_rate_last_month), 2)
    fr_trend = {
                'title':'Task Failure Rate',
                'data': round(failure_rate_this_month, 2),
                'delta': failure_rate_delta,
                'moment': 'Since last month',
            }

    # image chart
    image_chart_data = get_chart_data('image')
    task_sum_chart_data = get_chart_data('task_result_sum')
    task_st_chart_data = get_chart_data('task_st_this_week')

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
        "image_chart_data": image_chart_data,
        "task_sum_chart_data": task_sum_chart_data,
        "task_st_chart_data": task_st_chart_data,
        "activity_list": activity_list,
    }
    return render(request, 'index.html', context)


def dashboard(request):
    now = datetime.now(timezone.utc)

    # total samples by month
    start_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_last_month = (start_of_this_month - timedelta(days=1)).replace(day=1)

    total_sample_this_month = Sample.objects.filter(
                time_created__gte=start_of_this_month,
                time_created__lt=now
            ).count()

    total_sample_last_month = Sample.objects.filter(
                time_created__gte=start_of_last_month,
                time_created__lt=start_of_this_month
            ).count()
    total_sample_delta = total_sample_this_month - total_sample_last_month
    sample_trend = {
                'title': 'Total Sample (this month)',
                'data': total_sample_this_month,
                'delta': total_sample_delta,
            }

    # total image by week
    start_of_week = now - timedelta(days=now.weekday())
    start_of_this_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    start_of_last_week = start_of_this_week - timedelta(days=7)
    end_of_last_week = start_of_this_week - timedelta(seconds=1)

    total_image_this_week = Image.objects.filter(
                release_date__gte=start_of_this_week,
                release_date__lt=now
            ).count()

    total_image_last_week = Image.objects.filter(
                release_date__gte=start_of_last_week,
                release_date__lt=end_of_last_week
            ).count()
    total_image_delta = total_image_this_week - total_image_last_week
    image_trend = {
                'title': 'Image Release (this Week)',
                'data': total_image_this_week,
                'delta': total_image_delta
            }

    # total tasks by month
    total_task_this_month = Task.objects.filter(
                time_trigger__gte=start_of_this_month,
                time_trigger__lt=now
            ).count()

    total_task_last_month = Task.objects.filter(
                time_trigger__gte=start_of_last_month,
                time_trigger__lt=start_of_this_month
            ).count()
    total_task_delta = total_task_this_month - total_task_last_month
    task_trend = {
                'title': 'Total Task (this month)',
                'data': total_task_this_month,
                'delta': total_task_delta
            }

    # task failure rate by week
    total_failed_task_this_month = Task.objects.filter(
                result=False,
                time_trigger__gte=start_of_this_month,
                time_trigger__lt=now
            ).count()

    total_failed_task_last_month = Task.objects.filter(
                result=False,
                time_trigger__gte=start_of_last_month,
                time_trigger__lt=start_of_this_month
            ).count()
    if total_task_last_month == 0:
        total_task_last_month = 1
    if total_task_this_month == 0:
        total_task_this_month = 1
    failure_rate_last_month = total_failed_task_last_month / total_task_last_month
    failure_rate_this_month = total_failed_task_this_month / total_task_this_month
    failure_rate_delta = round((failure_rate_this_month - failure_rate_last_month), 2)
    fr_trend = {
                'title':'Task Failure Rate (this month)',
                'data': round(failure_rate_this_month, 2),
                'delta': failure_rate_delta
            }

    # image chart
    image_chart_data = get_chart_data('image')
    task_sum_chart_data = get_chart_data('task_result_sum')
    task_st_chart_data = get_chart_data('task_st_this_week')

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

    # search for Task
    all_task = Task.objects.all()
    task_list = []

    for i in all_task:
        tsk = model_to_dict(i)
        tsk['type'] = i.task_category[0]
        tsk['platform_name'] = i.sample.platform
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

    context = {
        "trends": [sample_trend, image_trend, task_trend, fr_trend],
        "image_chart_data": image_chart_data,
        "task_sum_chart_data": task_sum_chart_data,
        "task_st_chart_data": task_st_chart_data,
        "activity_list": activity_list,
        "task_list": task_list,
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
        sample_list.append(sp)

    platforms = Platform.objects.all()

    for i in platforms:
        plat_info_list.append({
            'id': i.pk,
            'plat_name': i.name,
            })

    users = UserProfile.objects.all()

    for i in users:
        user_list.append({
            'id': i.user.id,
            'user_name': i.full_name,
            })

    context = {
        "sample_list": sample_list,
        "platform_list": plat_info_list,
        "user_list": user_list
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
        tsk['platform_name'] = i.sample.platform
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





