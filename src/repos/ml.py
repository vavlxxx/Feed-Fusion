from src.models import DatasetUploads, ClassificatorTraining
from src.repos.base import BaseRepo
from src.repos.mappers.mappers import DatasetUploadMapper, TrainingMapper
from src.schemas.ml import TrainingDTO
from src.schemas.samples import DatasetUploadDTO


class DatasetUploadRepo(BaseRepo[DatasetUploads, DatasetUploadDTO]):
    model = DatasetUploads
    mapper = DatasetUploadMapper


class TrainingRepo(BaseRepo[ClassificatorTraining, TrainingDTO]):
    model = ClassificatorTraining
    mapper = TrainingMapper
