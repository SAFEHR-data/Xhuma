import json
from urllib.request import Request

import xmltodict
from fastapi import APIRouter, HTTPException, Request, Response

from ..ccda.helpers import clean_soap, validateNHSnumber
from ..redis_connect import redis_connect
from .responses import iti_38_response, iti_39_response

router = APIRouter(prefix="/SOAP")
client = redis_connect()

NAMESPACES = (
    {
        "http://www.w3.org/2003/05/soap-envelope": None,
        "http://www.w3.org/2005/08/addressing": None,
        "urn:oasis:names:tc:ebxml-regrep:xsd:query:3.0": None,
        "urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0": None,
        "urn:ihe:iti:xds-b:2007": None,
    },
)


@router.post("/iti47")
async def iti41(request: Request):
    content_type = request.headers["Content-Type"]
    if content_type == "application/xml":
        body = await request.body()
        envelope = clean_soap(body)
        # print(envelope)
        try:
            payload = envelope["Body"]["PRPA_IN201305UV02"]
        except:
            raise HTTPException(status_code=404, detail="ITI-47499 message not found")

        control_act = payload["controlActProcess"]
        query_id = control_act["queryByParameter"]["queryId"]
        query_params = control_act["queryByParameter"]["parameterList"]

        demographics = {
            "livingSubjectId": None,
            "livingSubjectAdministrativeGender": None,
            "livingSubjectName": None,
            "livingSubjectBirthTime": None,
        }

        for i in query_params:
            if i in demographics:
                demographics[i] = query_params[i]
        print(demographics)
        
        #TODO check for valid nhs number
        #TODO perform fhir pda enquiry

        return demographics
    else:
        raise HTTPException(
            status_code=400, detail=f"Content type {content_type} not supported"
        )


@router.post("/iti39")
async def iti39(request: Request):
    content_type = request.headers["Content-Type"]
    if content_type == "application/xml":
        body = await request.body()
        envelope = clean_soap(body)
        try:
            document_id = envelope["Body"]["RetrieveDocumentSetRequest"][
                "DocumentRequest"
            ]["DocumentUniqueId"]
        except:
            raise HTTPException(status_code=404, detail=f"DocumentUniqueId not found")

        document = client.get(document_id)
        if document is not None:
            # return ITI39 response
            message_id = envelope["Header"]["MessageID"]
            data = await iti_39_response(message_id, document_id, document)
            return Response(content=data, media_type="application/xml")
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Document with Id {document_id} not found or is empty",
            )
    else:
        raise HTTPException(
            status_code=400, detail=f"Content type {content_type} not supported"
        )


@router.post("/iti38")
async def iti38(request: Request):
    content_type = request.headers["Content-Type"]
    if content_type == "application/xml":
        body = await request.body()
        envelope = clean_soap(body)
        soap_body = envelope["Body"]
        slots = soap_body["AdhocQueryRequest"]["AdhocQuery"]["Slot"]
        query_id = soap_body["AdhocQueryRequest"]["AdhocQuery"]["@id"]
        patient_id = next(
            x["ValueList"]["Value"]
            for x in slots
            if x["@name"] == "$XDSDocumentEntryPatientId"
        )
        data = await iti_38_response(patient_id, query_id)
        return Response(content=data, media_type="application/xml")
    else:
        raise HTTPException(
            status_code=400, detail=f"Content type {content_type} not supported"
        )
