from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MaxValueValidator


class UserProfile(models.Model):
    """
    Class definition of UserProfile
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.CharField(max_length=80, default='default')
    extra_info = models.CharField(max_length=200, null=True, blank=True)
    
    @property
    def full_name(self):
        return "{} {}".format(self.user.first_name, self.user.last_name)

    class Meta:
        verbose_name = 'User Profile'

    def __str__(self):
        return "<{}: {}  [{}]>".format(
            self.user.id,
            self.user.username,
            self.full_name
        )


class Status(models.Model):
    """
    Class definition of Sample Status
    Status code: 2 digits XY
        X - 0: Offline
        X - 1: Online
        X - 2: Unknown
        X - 3: Other (Reserved)
        Y - 0~9: Specific Status
    """
    STATUS_CHOISE = {
        '00': '(OFF) offline',
        '10': '(A) Available, and',
        '11': '(A) Available',
        '12': '(B) OS installing',
        '13': '(B) OS installed - (Fail)',
        '14': '(B) OS installed - (Success)',
        '15': '(B) Test running',
        '16': '(B) Test Complete - (Fail)',
        '17': '(B) Test Complete - (Sussess)',
        '18': '(B) Log uploading',
        '20': '(U) Unkonwn',
        '30': '(O) Other',
    }
    code = models.CharField(max_length=2, choices=[(k, v) for k, v in STATUS_CHOISE.items()], unique=True, default='20')

    @property
    def description(self):
        return self.STATUS_CHOISE.get(self.code, 'Unkown')

    def __str__(self):
        return "<{} - {}>".format(
            self.code,
            self.description,
        )


class Sample(models.Model):
    """
    Class definition of Sample
    """
    ip = models.GenericIPAddressField(protocol='IPv4')
    service_tag = models.CharField(max_length=8)
    ssid = models.CharField(
            max_length=4,
            validators=[
                RegexValidator(
                    regex=r'^[0-9a-fA-F]{4}',
                    message='Must be a 4-character hexadecimal value'
                    )
                ]
            )
    platform = models.CharField(max_length=30)
    sku = models.CharField(max_length=30)
    remark = models.CharField(max_length=20, null=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank=True, related_name='samples') 
    owner = models.ForeignKey(UserProfile, on_delete=models.PROTECT, null=True, blank=True, related_name='owned_samples')
    current_user = models.ForeignKey(UserProfile, on_delete=models.PROTECT, null=True, blank=True, related_name='sample_in_use')
    last_update = models.TimeField(auto_now_add=True)

    def __str__(self):
        return "<{}: {} ({})>".format(
            self.platform,
            self.sku,
            self.remark,
        )


class Image(models.Model):
    """
    Class definition of Image
    """
    CATEGORY_CHOICES = [
        ('edge', 'Edge'),
        ('next', 'Next'),
        ('proposed', 'Proposed'),
        ('', 'Production'),
    ]
    image_name = models.CharField(max_length=60, unique=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='', blank=True)
    image_version = models.PositiveIntegerField(validators=[MaxValueValidator(999)])
    kernel_version = models.CharField(max_length=30)
    release_date = models.TimeField(auto_now_add=True)
    file_path = models.CharField(max_length=200, blank=False)
    file_size = models.DecimalField(max_digits=4, decimal_places=2)
    # Temporarily allow non-unique sha256 hash, even same file in different filename
    sha256_hash = models.CharField(
        max_length=64,
        validators=[RegexValidator(regex=r'^[a-fA-F0-9]{64}$')]
    )

    def __str__(self):
        return "<{}-{} ({})>".format(
            self.category,
            self.image_version,
            self.kernel_version,
        )


class TaskHistory(models.Model):
    """
    Class definition of TaskHistory
    """
    TASK_CHOICES = [
        ('Install', 'OS installation'),
        ('Test', 'Test Case Running'),
        ('Full', 'OS installation and Test Case Running'),
    ]
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    task_category = models.CharField(max_length=10, choices=TASK_CHOICES, blank=False)
    result = models.BooleanField(default=True)
    trigger_by = models.ForeignKey(UserProfile, on_delete=models.PROTECT, null=True, blank=True, related_name="tasks")
    log = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return "<{}: {}-{}>".format(
            self.sample.sku,
            self.image.category,
            self.image.image_version,
        )


class TestCase(models.Model):
    """
    Class definition of TestCase
    """
    number = models.CharField(max_length=20, blank=False)
    case_name = models.CharField(max_length=20)
    description = models.CharField(max_length=50)
    steps = models.CharField(max_length=79)
    version = models.CharField(max_length=20)

    def __str__(self):
        return "<{}: {}>".format(
            self.number,
            self.case_name,
        )
