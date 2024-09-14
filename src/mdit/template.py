import mdit as _mdit
from mdit import data as _data


def covenant_code_of_conduct(contact_name: str, contact_url: str) -> str:
    template = _data.file.template("code_of_conduct", "contributor_covenant")
    content = template.format(contact=f"[{contact_name}]({contact_url})")
    return _mdit.document(body=content)
