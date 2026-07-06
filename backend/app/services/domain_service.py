from typing import List, Optional
from app.models.domain import DomainCategory

# Mapping of keywords to domains
DOMAIN_KEYWORDS = {
    DomainCategory.TECH: [
        "software engineer", "developer", "data analyst", "ai engineer", "ml engineer",
        "devops", "cloud", "cybersecurity", "qa", "it support", "database", "frontend",
        "backend", "fullstack", "programming", "technology", "python", "java", "react"
    ],
    DomainCategory.LAW: [
        "lawyer", "legal associate", "legal counsel", "compliance", "paralegal",
        "contracts", "litigation", "law", "attorney"
    ],
    DomainCategory.HR: [
        "recruiter", "hr executive", "talent acquisition", "people operations",
        "payroll", "hr business partner", "human resources", "talent"
    ],
    DomainCategory.FINANCE: [
        "accountant", "auditor", "analyst", "tax", "banking", "investment",
        "accounts payable", "accounts receivable", "finance", "financial"
    ],
    DomainCategory.SALES_MARKETING: [
        "sales", "business development", "digital marketing", "seo", "content",
        "brand", "growth", "marketing", "b2b", "b2c", "account executive"
    ],
    DomainCategory.OPERATIONS_ADMIN: [
        "operations", "admin", "office manager", "coordinator", "supply chain",
        "procurement", "logistics", "administrative"
    ],
    DomainCategory.HEALTHCARE: [
        "doctor", "nurse", "pharmacist", "medical assistant", "clinical",
        "hospital", "healthcare", "medical", "patient"
    ],
    DomainCategory.ENGINEERING_MANUFACTURING: [
        "mechanical", "civil", "electrical", "production", "quality engineer",
        "plant", "manufacturing", "industrial", "hardware"
    ],
    DomainCategory.EDUCATION: [
        "teacher", "trainer", "lecturer", "academic", "coordinator", "education",
        "instructor", "tutor", "school"
    ],
    DomainCategory.DESIGN_PRODUCT: [
        "ui/ux", "graphic design", "product manager", "product designer",
        "designer", "user experience", "creative", "figma"
    ]
}

def _classify_text(text: str) -> DomainCategory:
    if not text:
        return DomainCategory.OTHER
    
    text = text.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return domain
    return DomainCategory.OTHER

def normalize_job_domain(title: str, department: Optional[str] = None, description: Optional[str] = None, skills: Optional[List[str]] = None) -> DomainCategory:
    """Classify a job into a broad domain category based on its attributes."""
    combined_text = title
    if department:
        combined_text += f" {department}"
    if skills:
        combined_text += f" {' '.join(skills)}"
    
    # Try title/department/skills first
    domain = _classify_text(combined_text)
    if domain != DomainCategory.OTHER:
        return domain
        
    # Fallback to description
    if description:
        return _classify_text(description)
        
    return DomainCategory.OTHER

def normalize_candidate_domain(title: Optional[str] = None, skills: Optional[List[str]] = None, education: Optional[str] = None, text: Optional[str] = None) -> DomainCategory:
    """Classify a candidate into a broad domain category based on their attributes."""
    combined_text = ""
    if title:
        combined_text += f"{title} "
    if skills:
        combined_text += f"{' '.join(skills)} "
    
    domain = _classify_text(combined_text)
    if domain != DomainCategory.OTHER:
        return domain
        
    if text:
        domain = _classify_text(text[:5000]) # First 5000 chars
        if domain != DomainCategory.OTHER:
            return domain
            
    return DomainCategory.OTHER
