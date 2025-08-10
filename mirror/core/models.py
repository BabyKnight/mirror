from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MaxValueValidator
from django.utils import timezone


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


class Sample(models.Model):
    """
    Class definition of Sample
    """
    STATUS_CHOISE = {
        '00': '(OFF) offline',
        '10': '(AVL) Available',
        '11': '(BSY) OS installing',
        '12': '(BSY) Log uploading',
        '13': '(BSY) TestCase running',
        '20': '(UNK) Unkonwn',
    }
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
    status = models.CharField(max_length=2, choices=[(k, v) for k, v in STATUS_CHOISE.items()], default='20')
    owner = models.ForeignKey(UserProfile, on_delete=models.PROTECT, null=True, blank=True, related_name='owned_samples')
    current_user = models.ForeignKey(UserProfile, on_delete=models.PROTECT, null=True, blank=True, related_name='sample_in_use')
    time_created = models.DateTimeField(default=timezone.now)
    last_update = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('service_tag', 'ssid')

    @property
    def status_desc(self):
        return self.STATUS_CHOISE.get(self.status, '20')

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
        ('production', 'Production'),
    ]
    image_name = models.CharField(max_length=60, unique=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='', blank=True)
    image_version = models.PositiveIntegerField(validators=[MaxValueValidator(999)])
    kernel_version = models.CharField(max_length=30)
    release_date = models.DateTimeField(default=timezone.now)
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


class Task(models.Model):
    """
    Class definition of Task
    """
    TASK_CHOICES = [
        ('i', 'OS installation'),
        ('t', 'Test Case Running'),
        ('f', 'OS installation and Test Case Running'),
    ]
    STATUS_CHOICES = [
        ('11', 'Pending'),
        ('12', 'Running'),
        ('13', 'Complete'),
        ('00', 'Unkonwn'),
    ]
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    task_category = models.CharField(max_length=10, choices=TASK_CHOICES, blank=False)
    result = models.BooleanField(default=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=False, default='00')
    trigger_by = models.ForeignKey(UserProfile, on_delete=models.PROTECT, null=True, blank=True, related_name="tasks")
    time_trigger = models.DateTimeField(default=timezone.now)
    time_start = models.DateTimeField(null=True, blank=True)
    time_complete = models.DateTimeField(null=True, blank=True)
    log = models.CharField(max_length=50, null=True, blank=True)

    @property
    def status_desc(self):
        return dict(self.STATUS_CHOICES).get(self.status, '11')

    def __str__(self):
        return "<{}: {}-{}>".format(
            self.sample.sku,
            self.image.category,
            self.image.image_version,
        )


class Platform(models.Model):
    """
    Class definition of Platform
    """
    name = models.CharField(max_length=30, unique=True)
    mkt_name = models.CharField(max_length=60)
    category = models.CharField(max_length=10)

    def __str__(self):
        return "<{}>".format(
            self.name,
        )


class TestCase(models.Model):
    """
    Class definition of TestCase
    """
    number = models.CharField(max_length=20, blank=False)
    case_name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    steps = models.CharField(max_length=79)
    version = models.CharField(max_length=20)

    def __str__(self):
        return "<{}: {}>".format(
            self.number,
            self.case_name,
        )
