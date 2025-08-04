#utils.py defines common method or utilities

from .models import Sample, Image, Task, TestCase
from datetime import datetime, timezone, timedelta
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncDate


def get_chart_data(chart_type):
    """
    method to get chart data by chart type
    Availble chart type:
        - platform
        - image
        - task_result_sum
        - task_st_this_week
    """

    # time defined for filter
    now = datetime.now(timezone.utc)
    first_day_of_month = now.replace(day=1)
    start_of_week = now - timedelta(days=now.weekday())
    six_month_ago = now - timedelta(days=180)

    label = []

    if chart_type == 'image':

        # label for the bar chart (past 6 month)
        past_6_month = []
        label_m = []
        for i in range(6):
            month_date = now - timedelta(days=(30 * i))
            label_m.append(month_date.strftime('%b'))
        past_6_month = label_m[::-1]
        label = past_6_month

        # category list
        cat_list = []
        for i in Image.CATEGORY_CHOICES:
            cat_list.append(i[0])

        # Images released count statistics in last 6 month
        img_cat_info = Image.objects.filter(release_date__gte=six_month_ago).annotate(
            month=TruncMonth('release_date')).values('month', 'category').annotate(count=Count('id')).order_by('month', 'category')
        for i in img_cat_info:
            i['month'] = i['month'].strftime('%b')

        dataset = {}
        for i in cat_list:
            dataset[i] = [0] * 6
        for info_by_month in img_cat_info:
            dataset[info_by_month['category']][past_6_month.index(info_by_month['month'])] = info_by_month['count']
     
    elif chart_type == 'task_result_sum':

        # label for the bar chart (past 6 month)
        past_6_month = []
        label_m = []
        for i in range(6):
            month_date = now - timedelta(days=(30 * i))
            label_m.append(month_date.strftime('%b'))
        past_6_month = label_m[::-1]
        label = past_6_month

        task_types = []
        for i in Task.TASK_CHOICES:
            task_types.append(i[0])

        task_sum = Task.objects.filter(time_trigger__gte=six_month_ago).annotate(
            month=TruncMonth('time_trigger')).values('month', 'task_category').annotate(
                result_pass=Count('id', filter=Q(result=True)), result_fail=Count('id', filter=Q(result=False))).order_by('month', 'task_category')
        for i in task_sum:
            i['month'] = i['month'].strftime('%b')

        dataset = {}
        for i in task_types:
            dataset[i] = {
                'pass': [0] * 6,
                'fail': [0] * 6,
            }
        for i in task_sum:
            dataset[i['task_category']]['pass'][past_6_month.index(i['month'])] += i['result_pass']
            dataset[i['task_category']]['fail'][past_6_month.index(i['month'])] += i['result_fail']

        # count task_cat 'full' in 'install' and 'test' and remove task_cat 'full' (install and test)
        for key in dataset['f']:
            dataset['i'][key] = [data_i + data_f for data_i, data_f in zip(dataset['i'][key], dataset['f'][key])]
            dataset['t'][key] = [data_i + data_f for data_i, data_f in zip(dataset['t'][key], dataset['f'][key])]

    elif chart_type == 'task_st_this_week':

        # label for the chart (weekday)
        day_of_week = []
        for i in range(7):
            day = now - timedelta(days=i)
            day_of_week.append(day.strftime('%a'))
        label = day_of_week[::-1]

        dataset = [0] * 7

        task_per_day = Task.objects.filter(time_trigger__gte=start_of_week).annotate(
            day=TruncDate('time_trigger')).values('day').annotate(count=Count('id')).order_by('day')
        for i in task_per_day:
            dataset[label.index(i['day'].strftime('%a'))] = i['count']


    elif chart_type == 'platform':
        pass


    else:
        sample_added_this_month = Sample.objects.filter(time_created__gte=first_day_of_month)
        sample_count_this_month = sample_added_this_month.count()


        tsk_this_week = Task.objects.filter(time_trigger__gte=start_of_week)
        tsk_count_this_week = tsk_this_week.count()

    context = {
        "label": label,
        'dataset': dataset,
    }

    return context