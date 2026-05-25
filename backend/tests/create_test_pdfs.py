"""
Generate minimal test PDFs for ConstructOS backend tests.
Uses only Python stdlib — no external PDF library required.
"""
import os
import struct
import zlib

TEST_PDF_DIR = os.path.join(os.path.dirname(__file__), "test_pdfs")


def make_pdf(pages: list[str]) -> bytes:
    """Build a minimal but valid PDF with one text stream per page."""
    objects = []  # list of (obj_id, bytes)
    obj_id = 1

    # Each page: content stream + page dict
    page_ids = []
    for text in pages:
        # Content stream
        stream_data = f"BT /F1 12 Tf 50 750 Td ({text}) Tj ET".encode()
        stream_obj = (
            f"{obj_id} 0 obj\n"
            f"<< /Length {len(stream_data)} >>\n"
            f"stream\n"
        ).encode() + stream_data + b"\nendstream\nendobj\n"
        objects.append((obj_id, stream_obj))
        stream_id = obj_id
        obj_id += 1

        # Page dict
        page_obj = (
            f"{obj_id} 0 obj\n"
            f"<< /Type /Page /Parent 0 0 R /MediaBox [0 0 612 792]\n"
            f"   /Contents {stream_id} 0 R\n"
            f"   /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\n"
            f">>\nendobj\n"
        ).encode()
        objects.append((obj_id, page_obj))
        page_ids.append(obj_id)
        obj_id += 1

    # Pages dict
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    pages_obj = (
        f"{obj_id} 0 obj\n"
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>\n"
        f"endobj\n"
    ).encode()
    pages_id = obj_id
    objects.append((obj_id, pages_obj))
    obj_id += 1

    # Catalog
    catalog_obj = (
        f"{obj_id} 0 obj\n"
        f"<< /Type /Catalog /Pages {pages_id} 0 R >>\n"
        f"endobj\n"
    ).encode()
    catalog_id = obj_id
    objects.append((obj_id, catalog_obj))
    obj_id += 1

    # Fix parent refs in page dicts
    # Rebuild with correct pages_id
    rebuilt = []
    for oid, data in objects:
        data = data.replace(b"/Parent 0 0 R", f"/Parent {pages_id} 0 R".encode())
        rebuilt.append((oid, data))
    objects = rebuilt

    # Build body
    header = b"%PDF-1.4\n"
    body = header
    offsets = {}
    for oid, data in objects:
        offsets[oid] = len(body)
        body += data

    # xref
    xref_offset = len(body)
    xref = f"xref\n0 {obj_id}\n0000000000 65535 f \n"
    for i in range(1, obj_id):
        xref += f"{offsets[i]:010d} 00000 n \n"
    trailer = (
        f"trailer\n<< /Size {obj_id} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )
    return body + xref.encode() + trailer.encode()


def main():
    os.makedirs(TEST_PDF_DIR, exist_ok=True)

    # spec.pdf — multi-page specification document with construction content
    spec_pages = [
        "STRUCTURAL SPECIFICATION - Section 1: Concrete Slab Requirements",
        "Slab thickness shall be 200mm. Rebar spacing 150mm centres. Grade 32 MPa concrete.",
        "Section 2: Column Design. Columns 400x400mm. Rebar 16mm diameter at 200mm spacing.",
        "Section 3: Foundation. Strip footing 600mm wide 300mm deep. Bearing capacity 150 kPa.",
        "Section 4: Wall Construction. 200mm block wall. Mortar grade M5. Reinforced every 3rd course.",
    ]
    with open(os.path.join(TEST_PDF_DIR, "spec.pdf"), "wb") as f:
        f.write(make_pdf(spec_pages))
    print(f"Created spec.pdf ({len(spec_pages)} pages)")

    # blueprint.pdf — has conflicting specs vs spec.pdf
    blueprint_pages = [
        "STRUCTURAL DRAWINGS - Sheet A1: Slab Layout",
        "Slab thickness 150mm. Rebar 12mm at 200mm centres. Concrete Grade 25 MPa.",
        "Sheet A2: Column Schedule. Columns 300x300mm. Rebar 12mm at 250mm spacing.",
    ]
    with open(os.path.join(TEST_PDF_DIR, "blueprint.pdf"), "wb") as f:
        f.write(make_pdf(blueprint_pages))
    print(f"Created blueprint.pdf ({len(blueprint_pages)} pages)")

    # tiny.pdf — 1-page minimal doc
    with open(os.path.join(TEST_PDF_DIR, "tiny.pdf"), "wb") as f:
        f.write(make_pdf(["Minimal test document for ConstructOS unit tests."]))
    print("Created tiny.pdf (1 page)")

    # fake.txt — not a PDF
    with open(os.path.join(TEST_PDF_DIR, "fake.txt"), "w") as f:
        f.write("This is not a PDF file.\n")
    print("Created fake.txt")

    print(f"\nAll test files created in: {TEST_PDF_DIR}")


if __name__ == "__main__":
    main()
