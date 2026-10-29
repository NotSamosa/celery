import json
from rest_framework import serializers
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule


class PeriodicTaskListSerializer(serializers.ModelSerializer):
    schedule_type = serializers.SerializerMethodField()
    schedule_details = serializers.SerializerMethodField()

    class Meta:
        model = PeriodicTask
        fields = [
            'id',
            'name',
            'task',
            'enabled',
            'schedule_type',
            'schedule_details',
            'total_run_count',
            'last_run_at',
            'date_changed',
        ]

    def get_schedule_type(self, obj):
        if obj.interval:
            return 'interval'
        elif obj.crontab:
            return 'crontab'
        return 'other'

    def get_schedule_details(self, obj):
        if obj.interval:
            return f"Every {obj.interval.every} {obj.interval.period}"
        elif obj.crontab:
            return f"{obj.crontab.minute} {obj.crontab.hour} {obj.crontab.day_of_month} {obj.crontab.month_of_year} {obj.crontab.day_of_week} ({obj.crontab.timezone})"
        return None


class DynamicScheduleCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=True)
    task = serializers.CharField(max_length=200, required=True)
    enabled = serializers.BooleanField(default=True)
    args = serializers.ListField(required=False, default=list)
    kwargs = serializers.DictField(required=False, default=dict)

    # Schedule type selector: 'interval' or 'crontab'
    schedule_type = serializers.ChoiceField(choices=['interval', 'crontab'], required=True)

    # Interval fields
    interval_every = serializers.IntegerField(required=False, min_value=1)
    interval_period = serializers.ChoiceField(
        choices=[
            ('seconds', 'Seconds'),
            ('minutes', 'Minutes'),
            ('hours', 'Hours'),
            ('days', 'Days'),
        ],
        required=False,
        default='seconds',
    )

    # Crontab fields
    crontab_minute = serializers.CharField(required=False, default='*')
    crontab_hour = serializers.CharField(required=False, default='*')
    crontab_day_of_week = serializers.CharField(required=False, default='*')
    crontab_day_of_month = serializers.CharField(required=False, default='*')
    crontab_month_of_year = serializers.CharField(required=False, default='*')
    crontab_timezone = serializers.CharField(required=False, default='Asia/Kolkata')

    def validate(self, data):
        st = data.get('schedule_type')
        if st == 'interval' and not data.get('interval_every'):
            raise serializers.ValidationError({"interval_every": "Required when schedule_type is 'interval'."})

        if PeriodicTask.objects.filter(name=data['name']).exists():
            raise serializers.ValidationError({"name": f"A periodic task with name '{data['name']}' already exists."})

        return data

    def create(self, validated_data):
        schedule_type = validated_data['schedule_type']
        name = validated_data['name']
        task = validated_data['task']
        enabled = validated_data.get('enabled', True)
        args = json.dumps(validated_data.get('args', []))
        kwargs = json.dumps(validated_data.get('kwargs', {}))

        if schedule_type == 'interval':
            interval, _ = IntervalSchedule.objects.get_or_create(
                every=validated_data['interval_every'],
                period=validated_data.get('interval_period', 'seconds'),
            )
            periodic_task = PeriodicTask.objects.create(
                interval=interval,
                name=name,
                task=task,
                args=args,
                kwargs=kwargs,
                enabled=enabled,
            )
        else:
            crontab, _ = CrontabSchedule.objects.get_or_create(
                minute=validated_data.get('crontab_minute', '*'),
                hour=validated_data.get('crontab_hour', '*'),
                day_of_week=validated_data.get('crontab_day_of_week', '*'),
                day_of_month=validated_data.get('crontab_day_of_month', '*'),
                month_of_year=validated_data.get('crontab_month_of_year', '*'),
                timezone=validated_data.get('crontab_timezone', 'Asia/Kolkata'),
            )
            periodic_task = PeriodicTask.objects.create(
                crontab=crontab,
                name=name,
                task=task,
                args=args,
                kwargs=kwargs,
                enabled=enabled,
            )

        return periodic_task

