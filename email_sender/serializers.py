from rest_framework import serializers


class SendEmailSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255, required=True)
    message = serializers.CharField(required=True)
    recipient_list = serializers.ListField(
        child=serializers.EmailField(),
        allow_empty=False,
        required=True,
    )
    html_message = serializers.CharField(required=False, allow_blank=True, default=None)


class BulkEmailSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255, required=True)
    message = serializers.CharField(required=True)
    recipient_list = serializers.ListField(
        child=serializers.EmailField(),
        allow_empty=False,
        required=True,
    )


class WelcomeEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(max_length=150, required=True)

