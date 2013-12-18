from django.db import models

# Create your models here.
class GroupBySample(models.Model):
    index_by_sample = models.IntegerField(default="Automatically generated")

    def get_count_by_sample(self):
        return self.__class__.objects.filter(**{self.sample_id_keyword:self.sample.id}).count()

    def get_max_by_sample(self):
        return self.__class__.objects.filter(
            **{self.sample_id_keyword:self.sample.id}).aggregate(
                models.Max('index_by_sample'))['index_by_sample__max']

    def save(self):
        if self.pk is None:
            self.index_by_sample = self.get_count_by_sample()
            if hasattr(self, 'character_list') \
              and self.index_by_sample >= len(self.character_list):
                raise(Exception("Too many objects, only %i %s supported by "
                                "naming scheme" % (len(self.character_list),
                                                   self.__class__)))
        super(GroupBySample, self).save()

    def index_to_naming_scheme(self):
        try:
            return self.character_list[self.index_by_sample]
        except IndexError:
            raise(Exception("Too many objects, only %i %s supported by naming"
                            "scheme" % (len(self.character_list),
                                        self.__class__)))

    class Meta:
        abstract = True

def property_verbose(description):
    """Make the function a property and give it a description. Normal property
    decoration does not work with short_description"""
    def property_verbose_inner(function):
        function.short_description = description
        return property(function)
    return property_verbose_inner

class Collaborator(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=100)
    email = models.EmailField()
    notes = models.TextField(blank=True)

    def __unicode__(self):
        return "%s %s" % (self.first_name, self.last_name)

class SampleType(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return "%s" % (self.name)

class SampleLocation(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return "%s" % (self.name)

class StorageLocation(models.Model):
    name = models.CharField(max_length=30)
    description = models.TextField(blank=False)

    def __unicode__(self):
        return "%s" % (self.name)

class Sample(models.Model):
    uid = models.CharField("UID", max_length=20, unique=True)

    collaborator = models.ForeignKey(Collaborator)
    sample_type = models.ForeignKey(SampleType)
    sample_location = models.ForeignKey(SampleLocation)
    storage_location = models.ForeignKey(StorageLocation, blank=True, null=True)

    temperature = models.DecimalField(u"Temperature \u00B0C", max_digits=10,
        decimal_places=2, blank=True, null=True)
    ph = models.DecimalField(" pH", max_digits=10, decimal_places=2, blank=True, null=True)
    salinity = models.DecimalField("Salinity unit(?))", max_digits=10, decimal_places=2, blank=True, null=True)
    depth = models.DecimalField("Depth (m)", max_digits=10, decimal_places=2, blank=True, null=True)
    gps = models.CharField("GPS", max_length=30, blank=True)
    shipping_method = models.CharField(max_length=30, blank=True)
    storage_medium = models.CharField(max_length=30, blank=True)
    date_received = models.DateField(blank=True)
    biosafety_level = models.IntegerField(
        choices=((1, 1), (2, 2), (3, 3), (4, 4)), blank=True, null=True)
    status = models.CharField(max_length=8,
        choices=(('new', 'new'), ('used', 'used'), ('finished','finished')), blank=True, null=True)
    notes = models.TextField(blank=True)

    @property
    def barcode(self):
        return "SA:" + str(self.uid)

    def __unicode__(self):
        return "%s" % (self.uid)

class Protocol(models.Model):
    name = models.CharField(max_length=30)
    revision = models.CharField(max_length=30)
    link = models.CharField(max_length=100)
    notes = models.TextField(blank=True)

    def __unicode__(self):
        return "%s" % (self.name)

class ExtractedCell(GroupBySample):
    sample = models.ForeignKey(Sample)
    protocol = models.ForeignKey(Protocol)
    storage_location = models.ForeignKey(StorageLocation)
    notes = models.TextField(blank=True)

    sample_id_keyword = "sample__id"

    @property
    def barcode(self):
        return "EC:%s" % str(self.uid)

    @property_verbose("UID")
    def uid(self):
        return "%s_%s" % (self.sample.uid, self.index_by_sample + 1)

    def __unicode__(self):
        return self.uid

class ExtractedDNA(GroupBySample):
    sample = models.ForeignKey(Sample, null=True, blank=True)
    protocol = models.ForeignKey(Protocol)
    storage_location = models.ForeignKey(StorageLocation)
    notes = models.TextField(blank=True)
    extracted_cell = models.ForeignKey(ExtractedCell, null=True, blank=True)

    sample_id_keyword = "sample__id"

    @property
    def barcode(self):
        return "ED:" + str(self.uid)

    @property_verbose("UID")
    def uid(self):
        return "%s_%s" % (self.sample.uid, self.index_by_sample + 1)

    def save(self):
        """Saves and checks whether either Sample or ExtractedCell is provided.
        Not both, because this makes it easier to change the Sample on an
        ExtractedCell for example. Otherwise you would have to change both this
        object and the Extracted Cell."""
        if bool(self.sample) != bool(self.extracted_cell):
            if self.sample:
                sample = self.sample
            else:
                sample = self.extracted_cell.sample
            super(ExtractedDNA, self).save()
        else:
            raise(Exception("You have to specify an Extracted cell or"
                            " a Sample, but not both."))

    class Meta:
        verbose_name = "Extracted DNA"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.uid

class QPCR(models.Model):
    report = models.CharField(max_length=100)

    class Meta:
        verbose_name = "QPCR"
        verbose_name_plural = "QPCRs"

    def __unicode__(self):
        return self.report

class RTMDA(models.Model):
    report = models.CharField(max_length=100)

    class Meta:
        verbose_name = "RT-MDA kinetics"
        verbose_name_plural = verbose_name

    def __unicode__(self):
        return self.report

class SAGPlate(GroupBySample):
    report = models.CharField(max_length=100)
    protocol = models.ForeignKey(Protocol)
    storage_location = models.ForeignKey(StorageLocation)
    notes = models.TextField(blank=True)
    extracted_cell = models.ForeignKey(ExtractedCell)
    rt_mda = models.ForeignKey(RTMDA)
    qpcr = models.ForeignKey(QPCR)

    sample_id_keyword = "extracted_cell__sample__id"
    character_list = [chr(ord('A') + i) for i in range(26)] # [A-Z]

    @property
    def sample(self):
        return self.extracted_cell.sample

    @property
    def barcode(self):
        return "SP:" + str(self.uid)

    @property_verbose("UID")
    def uid(self):
        return self.extracted_cell.sample.uid + \
            self.index_to_naming_scheme()

    class Meta:
        verbose_name = "SAG plate"
        verbose_name_plural = verbose_name + "s"

    def __unicode__(self):
        return self.uid

class SAGPlateDilution(GroupBySample):
    sag_plate = models.ForeignKey(SAGPlate)
    dilution = models.CharField(max_length=100)
    qpcr = models.ForeignKey(QPCR)

    sample_id_keyword = "extracted_cell__sample__id"
    character_list = [chr(ord('a') + i) for i in range(26)] + range(10) # [a-z0-9]

    @property
    def sample(self):
        return self.extracted_cell.sample

    @property
    def barcode(self):
        return "SP:" + str(self.uid)

    @property_verbose("UID")
    def uid(self):
        return self.sag_plate.extracted_cell.sample.uid + \
            self.index_to_naming_scheme()

    class Meta:
        verbose_name = "SAG plate dilution"
        verbose_name_plural = verbose_name + "s"

    def __unicode__(self):
        return self.uid

class Metagenome(GroupBySample):
    extracted_dna = models.ForeignKey(ExtractedDNA)
    diversity_report = models.CharField(max_length=100)

    sample_id_keyword = "extracted_dna__sample__id"
    character_list = ["%02d" % i for i in range(100)] # [01-99]

    @property
    def sample(self):
        return self.extracted_dna.sample

    @property_verbose("UID")
    def uid(self):
        return self.extracted_dna.sample.uid + "A_X" + \
            self.index_to_naming_scheme()

    def __unicode__(self):
        return self.uid

class Primer(models.Model):
    sequence = models.TextField()
    storage_location = models.ForeignKey(StorageLocation)
    tmelt = models.DecimalField(u"tmelt (\u00B0C)", max_digits=10,
                                decimal_places=2)
    concentration = models.DecimalField(u"Concentration (mol L\u207B\u00B9)",
                                        max_length=100, max_digits=10,
                                        decimal_places=5)
    stock = models.PositiveIntegerField()

class Amplicon(models.Model):
    extracted_dna = models.ForeignKey(ExtractedDNA)
    diversity_report = models.CharField(max_length=100)
    buffer = models.CharField(max_length=100)
    notes = models.TextField()
    primer = models.ManyToManyField(Primer)

    sample_id_keyword = "extracted_dna__sample__id"

    @property
    def sample(self):
        return self.extracted_dna.sample

    @property_verbose("UID")
    def uid(self):
        return self.extracted_dna.sample.uid + "A_Y" + \
            self.index_to_naming_scheme()

    def __unicode__(self):
        return self.uid

class SAG(models.Model):
    sag_plate = models.ForeignKey(SAGPlate, null=True)
    sag_plate_dilution = models.ForeignKey(SAGPlateDilution, null=True)
    well = models.CharField(max_length=3)
    concentration = models.DecimalField(u"Concentration (mol L\u207B\u00B9)",
                                        max_length=100, max_digits=10,
                                        decimal_places=5)

    def save(self):
        if sum((bool(self.sag_plate_dilution),
                bool(self.sag_plate))) == 1:
            super(SAG, self).save()
        else:
            raise(Exception("You have to specify either a SAGPlate or a "
                            "SAGPlateDilution and not both"))
    class Meta:
        verbose_name = "SAG"
        verbose_name_plural = "SAGs"

    @property_verbose("UID")
    def uid(self):
        sag_uid = self.sag_plate.uid if self.sag_plate else \
            self.sag_plate_dilution.uid
        return "%s_%s" % (sag_uid, well)

    def __unicode__(self):
        return self.uid

class PureCulture(models.Model):
    extracted_dna = models.ForeignKey(ExtractedDNA)
    concentration = models.DecimalField(u"Concentration (mol L\u207B\u00B9)",
                                        max_length=100, max_digits=10,
                                        decimal_places=5)

    sample_id_keyword = "extracted_dna__sample__id"
    character_list = ["%02d" % i for i in range(100)] # [01-99]

    @property
    def sample(self):
        return self.extracted_dna.sample

    @property_verbose("UID")
    def uid(self):
        return self.extracted_dna.sample.uid + "A_Z" + \
            self.index_to_naming_scheme()

    def __unicode__(self):
        return self.uid

class DNALibrary(models.Model):
    amplicon = models.ForeignKey(Amplicon, null=True)
    metagenome = models.ForeignKey(Metagenome, null=True)
    sag = models.ForeignKey(SAG, null=True)
    pure_culture = models.ForeignKey(PureCulture, null=True)

    buffer = models.CharField(max_length=100)
    i7 = models.CharField(max_length=100)
    i5 = models.CharField(max_length=100)
    sample_name_on_platform = models.CharField(max_length=100)

    #fastq_files
    protocol = models.ForeignKey(Protocol)
    storage_location = models.ForeignKey(StorageLocation)

    def save(self):
        if sum((bool(self.amplicon),
                bool(self.metagenome),
                bool(self.sag),
                bool(self.pure_culture))) == 1:
            super(ExtractedDNA, self).save()
        else:
            raise(Exception("You have to specify a DNA source from either "
                            "Amplicon, Metagenome, SAG or Pure culture and not "
                            "more than one"))

    class Meta:
        verbose_name = "DNA library"
        verbose_name_plural = verbose_name[:-1] + "ies"

class SequencingRun(models.Model):
    date = models.DateField()
    machine = models.CharField(max_length=100)
    report = models.CharField(max_length=100)
    folder = models.CharField(max_length=100)
    notes = models.TextField()
    dna_library = models.ManyToManyField(DNALibrary)

    protocol = models.ForeignKey(Protocol)

class ReadFile(models.Model):
    folder = models.CharField(max_length=100)
    filename = models.CharField(max_length=100)
    pair = models.PositiveIntegerField(choices=((1, 1), (2, 2)))
    lane = models.PositiveIntegerField()
    read_count = models.PositiveIntegerField()
    dna_library = models.ForeignKey(DNALibrary)
    sequencing_run = models.ForeignKey(SequencingRun)