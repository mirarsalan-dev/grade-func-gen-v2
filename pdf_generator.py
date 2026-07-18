# pdf_generator.py
import io
import base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import config

def generate_single_result_to_buffer(name, gr_no, branch, subjects):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # --- HEADER ---
    c.setFillColorRGB(0.14, 0.38, 0.92) # Theme Blue
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 45, "THEEM COLLEGE OF ENGINEERING")
    
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 70, f"Department of {branch}")
    
    # --- STUDENT DETAILS ---
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 140, f"Student Name: {name.upper()}")
    c.drawString(50, height - 160, f"GR Number: {gr_no}")
            
    # --- MARKS TABLE ---
    data = [["SUBJECT", "CR", "TH", "IA", "TW", "OP", "TOTAL", "GRADE", "STATUS"]]
    total_cr = 0
    total_cg = 0
    
    for sub in subjects:
        data.append([
            sub.get("Name", ""),
            str(sub.get("Credits", 0)),
            str(sub.get("TH", 0)),
            str(sub.get("IA", 0)),
            str(sub.get("TW", 0)),
            str(sub.get("OP", 0)),
            str(sub.get("Total", 0)),
            str(sub.get("Grade", 0)),
            sub.get("Status", "")
        ])
        total_cr += int(sub.get("Credits", 0))
        total_cg += int(sub.get("CG", 0))
        
    sgpa = round(total_cg / total_cr, 2) if total_cr > 0 else 0.0
    overall_status = "PASS" if all(sub.get("Status") == "PASS" for sub in subjects) else "FAIL"
    
    # Table Styling
    table = Table(data, colWidths=[140, 40, 40, 40, 40, 40, 50, 50, 60])
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor(config.C_PRIMARY)),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor(config.C_BG_CARD)),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor(config.C_BORDER)),
        ('ALIGN', (0,1), (0,-1), 'LEFT'),
    ])
    table.setStyle(style)
    
    table.wrapOn(c, width, height)
    table.drawOn(c, 40, height - 240 - (len(data)*20))
    
    # --- FOOTER STATS ---
    y_pos = height - 280 - (len(data)*20)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_pos, f"Total Credits: {total_cr}")
    
    display_sgpa = str(sgpa) if overall_status == "PASS" else "--"
    c.drawString(200, y_pos, f"SGPA: {display_sgpa}")
    
    status_color = colors.green if overall_status == "PASS" else colors.red
    c.setFillColor(status_color)
    c.drawString(400, y_pos, f"RESULT: {overall_status}")
    
    c.save()
    buffer.seek(0)
    return buffer

def generate_batch_results_to_buffer(semester_name, students_dict):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    for gr_no, data in students_dict.items():
        name = data.get("Name", "Unknown")
        subjects = data.get("Subjects", [])
        
        # --- HEADER ---
        c.setFillColorRGB(0.14, 0.38, 0.92) 
        c.rect(0, height - 100, width, 100, fill=1, stroke=0)
        
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2, height - 45, "THEEM COLLEGE OF ENGINEERING")
        
        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2, height - 70, "Department of Information Technology")
        
        # --- STUDENT DETAILS ---
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 140, f"Student Name: {name.upper()}")
        c.drawString(50, height - 160, f"GR Number: {gr_no}")
        
        # --- MARKS TABLE ---
        table_data = [["SUBJECT", "CR", "TH", "IA", "TW", "OP", "TOTAL", "GRADE", "STATUS"]]
        total_cr = 0
        total_cg = 0
        
        stored_sgpa = data.get("SGPA", "0.0")
        overall_status = data.get("Status", "PENDING")
        
        for sub in subjects:
            table_data.append([
                sub.get("Name", ""),
                str(sub.get("Credits", 0)),
                str(sub.get("TH", 0)),
                str(sub.get("IA", 0)),
                str(sub.get("TW", 0)),
                str(sub.get("OP", 0)),
                str(sub.get("Total", 0)),
                str(sub.get("Grade", 0)),
                sub.get("Status", "")
            ])
            total_cr += int(sub.get("Credits", 0))
            total_cg += int(sub.get("CG", 0))
            
        if total_cr > 0:
            sgpa = str(round(total_cg / total_cr, 2))
            overall_status = "PASS" if all(sub.get("Status") == "PASS" for sub in subjects) else "FAIL"
        else:
            sgpa = str(stored_sgpa)
            table_data.append(["No marks found in database", "-", "-", "-", "-", "-", "-", "-", "-"])
        
        # Table Styling
        table = Table(table_data, colWidths=[140, 40, 40, 40, 40, 40, 50, 50, 60])
        style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor(config.C_PRIMARY)),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor(config.C_BG_CARD)),
            ('TEXTCOLOR', (0,1), (-1,-1), colors.black), 
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,1), (0,-1), 'LEFT'), 
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor(config.C_BORDER)),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ])
        table.setStyle(style)
        table.wrapOn(c, width, height)
        table.drawOn(c, 40, height - 240 - (len(table_data)*20))
        
        # --- FOOTER STATS ---
        y_pos = height - 280 - (len(table_data)*20)
        
        c.setFillColorRGB(0, 0, 0) 
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_pos, f"Total Credits: {total_cr if total_cr > 0 else '-'}")
        
        display_sgpa = str(sgpa) if overall_status == "PASS" else "--"
        c.drawString(200, y_pos, f"SGPA: {display_sgpa}")
        
        status_color = colors.green if overall_status == "PASS" else colors.red
        c.setFillColor(status_color)
        c.drawString(400, y_pos, f"RESULT: {overall_status}")
        
        c.showPage()  
        
    c.save()
    buffer.seek(0)
    return buffer