import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_resume(filename, name, title, summary, experience, education, github=""):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []
    
    Story.append(Paragraph(f"<b>{name}</b>", styles["Heading1"]))
    Story.append(Paragraph(title, styles["Heading2"]))
    if github:
        Story.append(Paragraph(f"GitHub: {github}", styles["Normal"]))
    Story.append(Spacer(1, 12))
    
    Story.append(Paragraph("<b>Summary</b>", styles["Heading3"]))
    Story.append(Paragraph(summary, styles["Normal"]))
    Story.append(Spacer(1, 12))
    
    Story.append(Paragraph("<b>Experience</b>", styles["Heading3"]))
    for exp in experience:
        Story.append(Paragraph(exp, styles["Normal"]))
        Story.append(Spacer(1, 6))
    Story.append(Spacer(1, 12))
    
    Story.append(Paragraph("<b>Education</b>", styles["Heading3"]))
    for edu in education:
        Story.append(Paragraph(edu, styles["Normal"]))
        Story.append(Spacer(1, 6))
        
    doc.build(Story)

if __name__ == "__main__":
    arjun_exp = [
        "<b>Backend Developer</b> at TechSolutions (2022 - Present)",
        "Developed APIs using Python and FastAPI. Managed database migrations and wrote unit tests for backend services.",
        "<b>Junior Developer</b> at WebCorp (2020 - 2022)",
        "Assisted in maintaining legacy PHP applications and writing basic SQL queries."
    ]
    arjun_edu = [
        "B.S. in Computer Science - State University (2020)"
    ]
    create_resume("arjun_resume.pdf", "Arjun Patel", "Backend Developer", 
                  "Backend developer with 4 years of experience building APIs. Passionate about coding and learning new technologies.", 
                  arjun_exp, arjun_edu, github="arjunpatel-dev")
                  
    weak_exp = [
        "<b>IT Support Specialist</b> at HelpDesk Inc (2019 - Present)",
        "Resolved user tickets, installed software, and managed active directory.",
        "<b>Intern</b> at TechCorp (2018 - 2019)",
        "Basic HTML and CSS updates."
    ]
    weak_edu = [
        "B.A. in Communications - City College (2018)"
    ]
    create_resume("weak_candidate.pdf", "Sarah Jenkins", "IT Support / Web Intern", 
                  "Enthusiastic IT professional looking to transition into software development.", 
                  weak_exp, weak_edu, github="sjenkins99")

    enterprise_exp = [
        "<b>Senior Java Developer</b> at MegaCorp Financial (2015 - Present)",
        "Architected enterprise Java Spring Boot applications. Managed teams of 10+ developers. Specialized in Oracle DB optimization.",
        "<b>Java Developer</b> at Enterprise Systems LLC (2010 - 2015)",
        "Maintained monolithic Java applications and SOAP APIs."
    ]
    enterprise_edu = [
        "M.S. in Software Engineering - Tech Institute (2010)",
        "B.S. in Computer Science - Tech Institute (2008)"
    ]
    create_resume("enterprise_candidate.pdf", "Dr. David Kim", "Senior Java Enterprise Developer", 
                  "Enterprise software architect with 15 years of experience in Java, Spring Boot, and Oracle databases. Proven track record in highly regulated financial environments.", 
                  enterprise_exp, enterprise_edu, github="davidkim-enterprise")
