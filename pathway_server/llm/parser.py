import json
from typing import Annotated, Generic, Optional
from typing_extensions import override

import pydantic
from pydantic import SkipValidation
from langchain_core.output_parsers import (
    PydanticOutputParser as PydanticOutputParser_lng,
)
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.outputs import Generation
from langchain_core.utils.pydantic import PYDANTIC_MAJOR_VERSION, TBaseModel
from langchain_community.llms.replicate import Replicate

from utils import log_message


class PydanticOutputParser(JsonOutputParser, Generic[TBaseModel]):
    llm: Replicate

    """Parse an output using a pydantic model."""
    pydantic_object: Annotated[type[TBaseModel], SkipValidation()]  # type: ignore
    """The pydantic model to parse."""

    def _parse_obj(self, obj: dict) -> TBaseModel:
        if PYDANTIC_MAJOR_VERSION == 2:
            try:
                if issubclass(self.pydantic_object, pydantic.BaseModel):
                    return self.pydantic_object.model_validate(obj)
                elif issubclass(self.pydantic_object, pydantic.v1.BaseModel):
                    return self.pydantic_object.parse_obj(obj)
                else:
                    msg = f"Unsupported model version for PydanticOutputParser: \
                            {self.pydantic_object.__class__}"
                    raise OutputParserException(msg)
            except (pydantic.ValidationError, pydantic.v1.ValidationError) as e:
                raise self._parser_exception(e, obj) from e
        else:  # pydantic v1
            try:
                return self.pydantic_object.parse_obj(obj)
            except pydantic.ValidationError as e:
                raise self._parser_exception(e, obj) from e

    def _parser_exception(
        self, e: Exception, json_object: dict
    ) -> OutputParserException:
        json_string = json.dumps(json_object)
        name = self.pydantic_object.__name__
        msg = f"Failed to parse {name} from completion {json_string}. Got: {e}"
        return OutputParserException(msg, llm_output=json_string)

    @override
    def parse_result(
        self, result: list[Generation], *, partial: bool = False
    ) -> Optional[TBaseModel]:
        """Parse the result of an LLM call to a pydantic object.

        Args:
            result: The result of the LLM call.
            partial: Whether to parse partial JSON objects.
                If True, the output will be a JSON object containing
                all the keys that have been returned so far.
                Defaults to False.

        Returns:
            The parsed pydantic object.
        """
        try:
            json_object = super().parse_result(result)
            return self._parse_obj(json_object)
        except:
            parser = PydanticOutputParser_lng(pydantic_object=self.pydantic_object)
            try:
                log_message("using output fixer")
                from langchain.output_parsers import OutputFixingParser

                new_parser = OutputFixingParser.from_llm(
                    parser=parser, llm=self.llm, max_retries=2
                )
                return new_parser.parse(result[0].text)
            except Exception as e:
                log_message(f"Output_fixer_error {e}")
                log_message("Parsed JSON object:", result[0].text)
                return parser.parse(result[0].text)

    @override
    def parse(self, text: str) -> TBaseModel:
        """Parse the output of an LLM call to a pydantic object, with optional fallback."""
        return super().parse(text)

    def get_format_instructions(self) -> str:
        """Return the format instructions for the JSON output.

        Returns:
            The format instructions for the JSON output.
        """
        # Copy schema to avoid altering original Pydantic schema.
        schema = dict(self.pydantic_object.model_json_schema().items())

        # Remove extraneous fields.
        reduced_schema = schema
        if "title" in reduced_schema:
            del reduced_schema["title"]
        if "type" in reduced_schema:
            del reduced_schema["type"]
        # Ensure json in context is well-formed with double quotes.
        schema_str = json.dumps(reduced_schema, ensure_ascii=False)

        return _PYDANTIC_FORMAT_INSTRUCTIONS.format(schema=schema_str)

    @property
    def _type(self) -> str:
        return "pydantic"

    @property
    @override
    def OutputType(self) -> type[TBaseModel]:
        """Return the pydantic model."""
        return self.pydantic_object


PydanticOutputParser.model_rebuild()
_PYDANTIC_FORMAT_INSTRUCTIONS = """The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of the schema. The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.

Here is the output schema:
```
{schema}
```"""  # noqa: E501
