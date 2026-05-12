from pydantic import BaseModel, ConfigDict

from schemas.utils.to_camel import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )
