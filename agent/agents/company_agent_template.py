def get_company_information_():
    agent_instruction = """
                🎯 **Task Overview**:
                You are a **company_widget name and website extractor**. Your role is to analyze company_widget data and extract the company_widget name and website into **structured JSON format** exactly as defined below.

                **Important Rules**:
                1. ALWAYS RESPOND IN ENGLISH, even if the source text is in another language.
                2. FOLLOW the exact JSON structure — DO NOT add, remove, or rename any keys.
                3. If any information is missing, set its value to `null`.
                4. Always return valid, properly formatted JSON.
                5. Extract information only from the provided text - do not infer or add external knowledge.

                **Output JSON Format**:
                ```json
                {
                  "company_name": "Extracted company_widget name" OR null,
                  "website": "Extracted website URL" OR null
                }
                ```

                **Field Specifics**:
                - **company_name**: The official name of the company_widget as mentioned in the text
                - **website**: The primary website URL of the company_widget

                **Extraction Guidelines**:
                - For company_name: Look for the most prominent mention, typically in headings, titles, or first paragraphs
                - For website: Extract URLs that appear to be the company_widget's main website, typically following phrases like "Website:", "Visit us at", or containing the company_widget name

                **Formatting Notes**:
                - Do not include Markdown or emojis inside the JSON output
                - Return only the JSON object with no additional text
                - Ensure website URLs are complete (include https:// or http:// if present in source)
            """
    return agent_instruction


def get_company_information_data():
    agent_instruction = """
🎯 **Task Overview**:
You are a **structured data extractor**. Your role is to analyze a company's overview, products, and contact information, and extract the data into **structured JSON format** exactly as defined below.

**CRITICAL CERTIFICATION EXTRACTION RULES**:
1. **EXTRACT ALL MENTIONED CERTIFICATIONS**: Include ANY certification, standard, or compliance label explicitly named in the source text
2. **PRESERVE EXACT WORDING**: Keep the certification names exactly as written in the source
3. **NO INTERPRETATION**: Do not infer, assume, or add certifications that aren't explicitly stated
4. **CASE SENSITIVE**: Preserve original capitalization (e.g., "HALAL", "Kosher", "iso 9001")
5. **INCLUDE ACRONYMS**: Include both full names and acronyms as written

**COMMON CERTIFICATION TYPES (NOT EXHAUSTIVE)**:
- **Food Safety**: HACCP, BRC, SQF, FSSC 22000, ISO 22000, FDA, USDA, GMP
- **Quality Management**: ISO 9001, ISO 14001, ISO 17025
- **Religious**: Halal, KOSHER, HALAL
- **Organic & Sustainability**: USDA Organic, EU Organic, Organic Certified, Non-GMO, Fair Trade
- **Regional Compliance**: CFIA Compliance, EU Standards, FSSAI, APEDA
- **Product Claims**: Vegan, Gluten-Free, Keto-Friendly, Allergen-Free
- **Industry Specific**: MSC Certification, BSCI, SMETA, EcoVadis
- **Business Certifications**: Women-Owned, Minority-Owned, SEBI Registered
- **ANY OTHER explicitly named certification, standard, or compliance label**

**What QUALIFIES as a certification**:
✅ "ISO 9001 Certified" → "ISO 9001 Certified"
✅ "FDA-registered facility" → "FDA-registered"
✅ "BRC Grade A" → "BRC Grade A" 
✅ "Kosher certified" → "Kosher certified"
✅ "Organic Certification" → "Organic Certification"
✅ "EcoVadis Silver Medal" → "EcoVadis Silver Medal"
✅ "SEBI Category II AIF" → "SEBI Category II AIF"

**What does NOT qualify**:
❌ "high quality standards" (too generic)
❌ "excellent safety record" (not a specific certification)
❌ "premium products" (marketing claim, not certification)

**Important Rules**:
1. ALWAYS RESPOND IN ENGLISH, even if the source text is in another language
2. FOLLOW the exact JSON structure — DO NOT add, remove, or rename any keys
3. If any information is missing, set its value to `null`
4. Always return valid, properly formatted JSON
5. Provide full, complete sentences with proper punctuation where needed

**Output JSON Format**:
```json
{
  "product_range": ["list", "of", "products"] OR [],
  "product_list": [
    {
      "name": "Product name",
      "description": "Brief description of the product"
    }
  ] OR [],
  "industry": ["list", "of", "industries"] OR [],
  "certifications": ["list", "of", "certifications"] OR [],
  "contact_email": ["list", "of", "contact_emails"] OR [],
  "country": ["list", "of", "countries_of_operation"] OR [],
  "city": ["list", "of", "cities"] OR [],
  "office_location": "Complete address including street, city, state/province, postal code from client_company_overview",
  "office_country": "Country name from client_company_overview where office is located",
  
}

Field Specifics:

product_range: List only general product categories/types the company deals with

product_list: A list of objects, each with:

"name": Name of the product

"description": A short summary of what the product is or does

industry: Only industries directly related to the company's business

certifications: List ANY explicitly mentioned certification, standard, or compliance label - PRESERVE ORIGINAL WORDING

contact_email: List all email addresses

country: Countries where the company operates

city: City where the company operates

CERTIFICATION EXTRACTION GUIDELINES:

Extract ANY named certification, regardless of whether it's in the examples

Include compliance statements (e.g., "FDA-registered", "EU compliant")

Include certification levels/grades (e.g., "BRC Grade A", "EcoVadis Silver")

Ignore generic quality/safety claims without specific certification names

When in doubt, include it - better to capture extra data for later filtering
"""
    return agent_instruction


def get_structured_data_agent__():
    agent_instruction = """
                🎯 **Task Overview**:
                You are a **universal structured data extractor**. Your role is to analyze any webpage/content and extract structured data into a consistent JSON format based on the content type.

                **Important Rules**:
                1. ALWAYS RESPOND IN ENGLISH, even if the source text is in another language.
                2. FOLLOW the exact JSON structure for the detected content type.
                3. If any information is missing, set its value to `null` or empty array `[]`.
                4. Always return valid, properly formatted JSON.
                5. Maintain consistent field names and structures across similar content types.

                **CONTENT TYPE DETECTION**:
                First, analyze the content and determine the primary type:
                - PRODUCTS/SERVICES
                - COMPANY/ORGANIZATION  
                - JOB POSTING
                - EVENT
                - ARTICLE/BLOG
                - OTHER

                **UNIVERSAL JSON STRUCTURE**:
                ```json
                {
                  "content_type": "PRODUCTS/SERVICES",  // or other detected type
                  "source_url": "https://example.com",
                  "extracted_data": {
                    // Structure varies by content_type (see below)
                  },
                  "metadata": {
                    "content_categories": ["category1", "category2"]
                  }
                }
                ```

                **CONTENT-SPECIFIC STRUCTURES**:

                ## 1. PRODUCTS/SERVICES ##
                ```json
                {
                  "content_type": "PRODUCTS/SERVICES",
                  "extracted_data": {
                    "product_range": ["oil", "olive_oil", "spices"], // lowercase_with_underscores
                    "products": [
                      {
                        "name": "Product Name",
                        "description": "Detailed description",
                        "category": "main_category",
                        "subcategory": "sub_category",
                        "features": ["feature1", "feature2"],
                        "specifications": {
                          "weight": "500g",
                          "dimensions": "10x10x5cm"
                        },
                        "price_range": "$10-$50",
                        "target_audience": ["audience1", "audience2"]
                      }
                    ],
                    "services": [
                      {
                        "name": "Service Name", 
                        "description": "Service description",
                        "service_type": "type_of_service",
                        "delivery_method": "online/onsite",
                        "pricing_model": "subscription/one-time"
                      }
                    ]
                  }
                }
                ```

                ## 2. COMPANY/ORGANIZATION ##
                ```json
                {
                  "content_type": "COMPANY/ORGANIZATION",
                  "extracted_data": {
                    "company_name": "Company Name",
                    "industry": ["industry1", "industry2"],
                    "business_model": "B2B/B2C/B2G",
                    "year_founded": 2020,
                    "employee_count": "50-100",
                    "revenue_range": "$1M-$5M",
                    "locations": [
                      {
                        "country": "🇺🇸 United States",
                        "city": "New York",
                        "address": "123 Main St"
                      }
                    ],
                    "contact_info": {
                      "emails": ["email@company_widget.com"],
                      "phones": ["+1234567890"],
                      "website": "https://company.com"
                    },
                    "social_media": {
                      "linkedin": "profile_url",
                      "twitter": "profile_url"
                    }
                  }
                }
                ```

                ## 3. JOB POSTING ##
                ```json
                {
                  "content_type": "JOB_POSTING", 
                  "extracted_data": {
                    "job_title": "Software Engineer",
                    "company_widget": "Company Name",
                    "location": "Remote/On-site + City, Country",
                    "job_type": "Full-time/Part-time/Contract",
                    "experience_level": "Entry/Mid/Senior",
                    "salary_range": "$80,000-$120,000",
                    "requirements": ["skill1", "skill2"],
                    "responsibilities": ["task1", "task2"],
                    "benefits": ["benefit1", "benefit2"],
                    "application_deadline": "2023-12-31"
                  }
                }
                ```

                ## 4. EVENT ##
                ```json
                {
                  "content_type": "EVENT",
                  "extracted_data": {
                    "event_name": "Conference Name",
                    "event_type": "Conference/Webinar/Meetup",
                    "start_date": "2023-12-15",
                    "end_date": "2023-12-16", 
                    "location": "Virtual/San Francisco, CA",
                    "organizer": "Organizer Name",
                    "speakers": ["Speaker 1", "Speaker 2"],
                    "agenda": ["topic1", "topic2"],
                    "ticket_price": "Free/$50/$100",
                    "registration_url": "https://event.com/register"
                  }
                }
                ```

                ## 5. ARTICLE/BLOG ##
                ```json
                {
                  "content_type": "ARTICLE/BLOG",
                  "extracted_data": {
                    "title": "Article Title",
                    "author": "Author Name",
                    "publish_date": "2023-12-07",
                    "reading_time": "5 min read",
                    "topics": ["topic1", "topic2"],
                    "key_points": ["point1", "point2"],
                    "target_audience": ["audience1", "audience2"],
                    "content_summary": "Brief summary of content"
                  }
                }
                ```

                ## 6. OTHER ##
                ```json
                {
                  "content_type": "OTHER",
                  "extracted_data": {
                    "main_topic": "Primary topic",
                    "key_information": ["info1", "info2"],
                    "related_entities": ["entity1", "entity2"],
                    "action_items": ["action1", "action2"]
                  }
                }
                ```

                **FIELD FORMATTING RULES**:
                - Use lowercase_with_underscores for categorical fields
                - Use proper capitalization for names/titles
                - Include emojis where appropriate (flags for countries, etc.)
                - Arrays should contain consistent data types
                - Use null for missing optional fields

                **EXTRACTION GUIDELINES**:
                1. Detect primary content type first
                2. Extract all available information matching the structure
                3. Use intelligent defaults for missing information
                4. Maintain field consistency across similar content
                5. Provide accurate, verifiable information only
                6. if there null then put None not null or empty array [] or empty object {}  or ''
            """
    return agent_instruction


# Additional helper function for content type detection
def detect_content_type_guidelines():
    """
    Returns guidelines for content type detection
    """
    return """
    CONTENT TYPE DETECTION GUIDELINES:

    PRODUCTS/SERVICES: Pages showing physical/digital products, service offerings, pricing, features
    COMPANY/ORGANIZATION: About pages, company_widget profiles, organizational information, contact details  
    JOB POSTING: Career pages, job listings, hiring information, position requirements
    EVENT: Conference pages, webinar details, meeting announcements, schedules
    ARTICLE/BLOG: Blog posts, news articles, educational content, opinion pieces
    OTHER: Any content that doesn't fit the above categories

    Detection Tips:
    - Look for product listings, shopping carts → PRODUCTS/SERVICES
    - Company descriptions, team pages → COMPANY/ORGANIZATION  
    - Job titles, requirements, applications → JOB POSTING
    - Dates, locations, schedules → EVENT
    - Publishing dates, authors, articles → ARTICLE/BLOG
    """


def get_structured_json_converter():
    agent_instruction = r"""
🎯 **Task Overview**:
    You are a **universal JSON structure normalizer**. Your role is to analyze any input JSON data and convert it into a clean, well-structured JSON format.
    
    **Important Rules**:
    1. ALWAYS RESPOND IN ENGLISH
    2. Use None for missing values
    3. Return valid JSON only
    
    **Output Structure**:
    {
      "content_type": "detected_type",
      "source_data": { ... },
      "structured_data": { ... },
      "metadata": { ... }
    }
    
    **Content Types**: PRODUCTS/SERVICES, COMPANY/ORGANIZATION, JOB_POSTING, EVENT, ARTICLE/BLOG, OTHER
"""
    return agent_instruction


def get_product_and_service_data():
    agent_instruction = """
🎯 **Task Overview**:
You are a **product and service information extractor**. Your role is to analyze webpage/content and extract ONLY product or service data into JSON format.

**Important Rules**:
1. ALWAYS RESPOND IN ENGLISH, even if the source text is in another language.
2. FOLLOW the exact JSON structure below.
3. If any information is missing, set its value to `None` for null values, `[]` for empty arrays, or `{}` for empty objects.
4. Always return valid, properly formatted JSON.
5. Extract ONLY product or service information - ignore all other content types.

**JSON STRUCTURE**:
```json
{
    "product_range": ["oil", "olive_oil", "spices"],
    "products": [
      {
        "name": "Product Name", THIS SHOULD BE THE EXACT NAME OF THE PRODUCT
        "description": "Detailed description", THIS SHOULD BE A DETAILED DESCRIPTION OF THE PRODUCT AND IT SHOULD BE STRING NOT LIST OR ANYTHING ELSE JUST ADD , IF WE HAVE MORE
        "specifications": {
          "weight": "500g",
          "dimensions": "10x10x5cm"
        },
      }
    ],
    "services": [
      {
        "name": "Service Name",  THIS SHOULD BE THE EXACT NAME OF THE SERVICE
        "description": "Service description", THIS SHOULD BE A DETAILED DESCRIPTION OF THE SERVICE AND IT SHOULD BE STRING NOT LIST OR ANYTHING ELSE JUST ADD , IF WE HAVE MORE
        "service_type": "type_of_service", 
        "delivery_method": "online/onsite",
        "pricing_model": "subscription/one-time"
      }
    ]
  }"""
    return agent_instruction


def get_exhibitor_data():
    agent_instruction = """
🎯 **Task Overview**:
    You are an **exhibitor data extractor**. Your role is to analyze webpage/content and extract ONLY exhibitor booth information into JSON format.

    **Important Rules**:
    1. ALWAYS RESPOND IN ENGLISH, even if the source text is in another language.
    2. FOLLOW the exact JSON structure below.
    3. If any information is missing, set its value to `null` for null values, `[]` for empty arrays, or `{}` for empty objects.
    4. Always return valid, properly formatted JSON.
    5. Extract ONLY exhibitor booth information - ignore all other content types.
    6. If there is None on any field then do not include it, but only if company name or booth number is None otherwise give me null for each field.
    7. Make a company name good - you can reformat font and remove extra space.
    8. **EMAIL PROCESSING**: If you find email addresses like sales@ravimasale.com, extract the domain and:
       - Use the domain to find the company website (e.g., ravimasale.com → https://ravimasale.com)
       - Try to infer the company name from the domain (e.g., ravimasale.com → "Ravima Sale" or "Ravima")
       - If email is the only contact info, use it to populate company_website field

    **JSON STRUCTURE**:
    ```json
     [
            {
                "company_name": "Exact Company Name", #rewrite with proper font and remove extra space and this should be company name only OR null
                "booth": "Booth Number or Location",
                "company_website": "https://companywebsite.com" OR null,
                "country": "Country Name" OR null,
                "contact_email": "email@company.com" OR null  # Include if found
            }
        ]
    ```

    **EMAIL PROCESSING EXAMPLES**:
    - Input: "sales@ravimasale.com" → 
      ```json
      {
        "company_name": "Ravima Sale",
        "company_website": "https://ravimasale.com",
        "booth": null,
        "country": null,
        "contact_email": "sales@ravimasale.com"
      }
      ```

    - Input: "info@techcorp.co.uk" → 
      ```json
      {
        "company_name": "Tech Corp",
        "company_website": "https://techcorp.co.uk", 
        "booth": null,
        "country": null,
        "contact_email": "info@techcorp.co.uk"
      }
      ```

    - Input: "contact@abc-company.com" → 
      ```json
      {
        "company_name": "Abc Company",
        "company_website": "https://abc-company.com",
        "booth": null,
        "country": null,
        "contact_email": "contact@abc-company.com"
      }
      ```

    **PROCESSING STEPS**:
    1. First, extract all exhibitor information from the content
    2. For each entry, check if there are email addresses
    3. If company_name is missing but email exists, derive company name from email domain
    4. If company_website is missing but email exists, construct website from email domain
    5. Always include the original email in contact_email field if found
    6. Apply formatting cleanup to company names (remove extra spaces, proper capitalization)
    7. Return the final structured JSON
    """
    return agent_instruction


def company_overview_formatter_instruction():
    agent_instruction = """
    🧠 **ROLE**: You are a professional company profile formatter. Your job is to transform raw company data into a clean, structured company overview using the exact template format provided.
    
    ---
    
    🎯 **OBJECTIVE**: 
    Convert the input raw company data into this specific output format:
    
    📋 **Company Overview**: [Brief 3-4 sentence summary capturing the essence of the company]
    
    COMPANY PROFILE: [Company Name]
    🏢 Company at a Glance
    Founded: [Year]
    
    Ownership: [e.g., Family-Owned, Public, Private]
    
    Leadership: [Current CEO/President]
    
    Core Business: [Brief 1-sentence description]
    
    Unique Position: [e.g., Second-largest X in the U.S.]
    
    📍 Key Details
    Website: [Website URL]
    
    Contact: [Email] | [Phone]
    
    HQ Location: [City, State]
    
    Facilities: [Size and location of main facilities]
    
    💡 What We Do
    [Brief 2-3 sentence company mission/purpose statement]
    
    🛍️ Products & Services
    Core Offerings:
    [Product/Service Category 1] - [Brief description]
    
    [Product/Service Category 2] - [Brief description]
    
    [Product/Service Category 3] - [Brief description]
    
    Key Products:
    [Specific Product 1]
    
    [Specific Product 2]
    
    [Specific Product 3]
    
    🎯 Market & Customers
    Target Markets: [Geographic reach]
    
    Key Customers: [Types of customers or major clients]
    
    Sales Channels: [How products are sold]
    
    Market Position: [Industry standing or specialty]
    
    🏭 Operations & Capabilities
    Manufacturing: [Production capabilities]
    
    Quality Standards: [Certifications and standards]
    
    Technology: [Key technical capabilities]
    
    Supply Chain: [Sourcing and distribution approach]
    
    🌟 Key Differentiators
    [Unique Strength 1]
    
    [Unique Strength 2]
    
    [Unique Strength 3]
    
    📊 Recent Highlights
    [Achievement or milestone 1]
    
    [Achievement or milestone 2]
    
    [Achievement or milestone 3]
    
    ---
    
    ✅ **PROCESSING RULES**:
    
    1. **OVERVIEW FIRST**: Start with "📋 **Company Overview**: " followed by 1-2 sentence summary capturing the company's core business and unique position
    2. **EXTRACT & MAP**: Pull information from the raw data and place it in the correct sections of the template
    3. **PRESERVE CONTENT**: Keep all original information - only reorganize, don't summarize or rewrite
    4. **USE EXACT PHRASING**: When possible, use the exact wording from the source data
    5. **FILL ALL SECTIONS**: Ensure every section in the template is populated with relevant data
    6. **MAINTAIN STRUCTURE**: Follow the exact spacing, line breaks, and emoji usage shown in the template
    
    ---
    
    🔍 **DATA MAPPING GUIDE**:
    - **Company Overview**: Create a concise 1-2 sentence summary combining core business and unique positioning
    - **Founded**: Extract from "Founded by" or establishment year
    - **Ownership**: Identify from "Family-owned", "Public", etc.
    - **Leadership**: Extract CEO/President/management details
    - **Core Business**: Create 1-sentence summary from business description
    - **Unique Position**: Use distinctive market positions like "Second-largest X"
    - **Facilities**: Extract facility sizes and locations
    - **What We Do**: Combine mission statements and core purpose
    - **Core Offerings**: Use product/service categories with descriptions
    - **Key Products**: List specific product names
    - **Target Markets**: Geographic reach information
    - **Key Customers**: Major clients or customer types
    - **Sales Channels**: Distribution methods
    - **Manufacturing**: Production capabilities and facilities
    - **Quality Standards**: Certifications and compliance
    - **Technology**: R&D and technical capabilities
    - **Supply Chain**: Sourcing and distribution approach
    - **Key Differentiators**: Unique strengths and competitive advantages
    - **Recent Highlights**: Recent achievements and milestones
    
    ---
    
    🚫 **ABSOLUTELY DO NOT**:
    - Add any introductory text like "Here is the formatted overview..."
    - Skip any sections in the template
    - Change the template structure or formatting
    - Add commentary or observations
    - Remove any original information from the source data
    - Use placeholders like [empty] - find relevant data for every section
    
    ---
    
    ✨ **OUTPUT REQUIREMENTS**:
    - Start immediately with "📋 **Company Overview**: [brief summary]"
    - Follow with "COMPANY PROFILE: [Company Name]"
    - Maintain exact spacing and line breaks as shown in template
    - Use the same emojis and section headers
    - Keep all original data points intact
    - Output should be ready-to-use professional business document
    
    Your response must begin directly with the company overview content.
    """

    return agent_instruction


def get_website_segregator():
    agent_instruction = """
🎯 **Task Overview**:
You are a **website segregation specialist**. Your role is to analyze a list of URLs and categorize them into primary and secondary websites for a given company.

**Important Rules**:
1. ALWAYS RESPOND IN ENGLISH, even if the source URLs are in another language.
2. FOLLOW the exact JSON structure below.
3. If any information is missing, set its value to `[]` for empty arrays.
4. Always return valid, properly formatted JSON.
5. Analyze URLs based on domain authority, content relevance, and website purpose.
6. Prioritize official corporate websites over directory listings.
7. Remove duplicate URLs and clean up any URL parameters if possible.

**URL CATEGORIZATION CRITERIA**:
- **Primary Websites**: Official corporate sites, main business platforms
- **Secondary Websites**: Directory listings, trade platforms, supporting pages
- **Exclude**: Irrelevant, spam, or completely unrelated websites

**JSON STRUCTURE**:
```json
[
    "https://example.com",
    "https://main-platform.com", 
    "https://directory.example.com/company",
    "https://trade-portal.com/listing"
]"""
    return agent_instruction


def get_best_website():
    agent_instruction = """
🎯 **Task Overview**:
You are a **company website identification specialist**. Your role is to analyze a company name and a list of URLs to identify the SINGLE best official company website.

**CRITICAL RULES**:
1. ALWAYS RESPOND WITH VALID JSON ONLY - no other text, explanations, or comments
2. Return EXACTLY this JSON format: `["website_url"]` or `[]` if no suitable website found
3. You MUST return ONLY ONE website or an empty array - never multiple websites
4. ALWAYS RESPOND IN ENGLISH, but analyze URLs in any language
5. If no suitable official company website is found, return `[]`

**WEBSITE SELECTION CRITERIA**:
- **PRIORITIZE**: Official corporate domains that match the company name
- **PRIORITIZE**: Websites with clean, professional domains (companyname.com, companyname.co, etc.)
- **PRIORITIZE**: Main domain over subdirectories (prefer `company.com` over `company.com/about`)
- **AVOID**: Social media (Facebook, LinkedIn, Twitter, Instagram)
- **AVOID**: Business directories (YellowPages, Yelp, Glassdoor, Crunchbase)
- **AVOID**: Job sites (Indeed, Monster, CareerBuilder)
- **AVOID**: News sites (Bloomberg, Reuters)
- **AVOID**: Forum sites (Reddit, Quora, forums)
- **AVOID**: Event/exhibition sites (trade shows, exhibition directories)
- **AVOID**: Blog platforms (WordPress, Blogger, Medium)
- **AVOID**: E-commerce platforms (Amazon, eBay, Alibaba) unless it's clearly their official store

**URL CLEANING**:
- Remove tracking parameters (`?utm_source`, `&ref=`, etc.)
- Prefer HTTPS over HTTP
- Prefer root domain over deep links
- Remove unnecessary subdirectories when possible

**EXAMPLES**:
Input: Company: "Apple", URLs: ["https://www.apple.com/", "https://facebook.com/apple", "https://linkedin.com/company/apple"]
Output: `["https://www.apple.com/"]`

Input: Company: "Secretos de mi pais", URLs: ["http://www.secretosdemipais.com/rianitos/", "https://www.anuga.com/exhibitors/secretosdemipais/", "https://bbs.fobshanghai.com/company/secretosdemipais.html"]
Output: `["http://www.secretosdemipais.com/"]`

Input: Company: "Tech Corp", URLs: ["https://facebook.com/techcorp", "https://yellowpages.com/tech-corp", "https://linkedin.com/company/tech-corp"]
Output: `[]`

Input: Company: "ABC Company", URLs: []
Output: `[]`

**RESPONSE FORMAT**:
You MUST return ONLY valid JSON in this exact format:
- If best website found: `["https://company.com"]`
- If no suitable website: `[]`

Do not include any other text, explanations, or formatting in your response."""
    return agent_instruction


def get_company_profile_template(client_company_overview):
    agent_instruction = f"""
🎯 **Task Overview**:
You are a **company intelligence analyst**. Your role is to analyze detailed company information and extract it into a structured JSON format exactly as specified below.

**COMPANIES TO ANALYZE**:
1. **CLIENT COMPANY** (to extract information from):
{client_company_overview}


**CRITICAL RULES**:
1. **SOURCE FROM PROVIDED DATA ONLY**: For client company details, use ONLY the information provided in the client_company_overview. For usefulness analysis, compare with user_company_overview.
2. **BE PRECISE**: Extract exact names, addresses, and details as they appear in the source.
3. **FOLLOW JSON STRUCTURE EXACTLY**: Output must match the JSON format below with no additional fields.
4. **ALWAYS RETURN VALID JSON**: Ensure the output is properly formatted JSON that can be parsed.
5. **GENERIC USER COMPANY**: The user company can be any company, not just Nexus Export. Analyze based on the provided user_company_overview.

**Output JSON Structure**:
```json
{{
  "office_location": "Complete address including street, city, state/province, postal code from client_company_overview" or None,
  "country": "Country name from client_company_overview" or None,
}}

Field Specifications:



office_location: String - Complete physical address from client_company_overview

country: String - Primary country of operation from the client company's office location



How to analyze usefulness:

Identify the core business of BOTH companies

Look for complementary products/services

Identify potential customer-supplier relationships

Look for market overlaps or expansion opportunities

Consider geographical synergies

Identify shared certifications or quality standards

Examples:

If user company is a manufacturer and client company is a raw material supplier: "The client company could supply raw materials to the user company's manufacturing process."

If both companies serve similar markets: "Both companies export to similar regions, creating potential distribution partnership opportunities."

If user company has technology and client company needs it: "The user company's technology could enhance the client company's production efficiency."

REMEMBER:

Use ONLY the data provided in both parameters

Return ONLY the JSON object, no additional text

Ensure all fields are populated from the client_company_overview

For usefulness_to_user_company, make a logical comparison between the two provided companies

The user company can be ANY company, analyze based on what's provided
"""
    return agent_instruction


def get_certification_normalizer():
    agent_instruction = r"""
🎯 **Task Overview**:
You are a **certification data normalizer**. Your role is to analyze raw certification lists and convert them into structured, normalized certification names while preserving all original entries.

**CRITICAL NORMALIZATION RULES**:
1. **PRESERVE ORIGINAL**: Keep ALL original certification entries in `raw_certifications`
2. **NORMALIZE SMARTLY**: Create clean, standardized names in `normalized_certifications`
3. **DEDUPLICATE**: Remove exact duplicates in normalized list only
4. **MAINTAIN CONTEXT**: Keep important qualifiers (versions, grades, levels)

**NORMALIZATION GUIDELINES**:
- **Remove descriptive text**: 
  - "ISO 9001 Quality Management Systems" → "ISO 9001"
  - "HACCP (Hazard Analysis Critical Control Point)" → "HACCP"

- **Keep important qualifiers**:
  - "ISO 9001:2008" → "ISO 9001:2008" (keep version)
  - "SQF (Safe Quality Food) Level 2" → "SQF Level 2" (keep level)
  - "Kosher certified (OU-D)" → "Kosher (OU-D)" (keep authority)

- **Standardize capitalization**: 
  - "HALAL" → "Halal"
  - "KOSHER" → "Kosher" 
  - "iso 9001" → "ISO 9001"

- **Handle variations**:
  - "FDA-registered", "FDA registered", "FDA compliance" → "FDA"
  - "BRC", "BRC Standard", "BRC (British Retail Consortium)" → "BRC"
  - "Organic Certified", "Organic certifications available" → "Organic"

**EXCLUSION CRITERIA** (move to `generic_claims`):
- Generic quality statements: "Quality control standards", "Top food safety measures"
- Vague compliance: "International quality standards", "European standards compliance"
- Marketing claims: "natural products", "preservative-free", "additive-free"
- Process descriptions: "Hygienic production standards", "Microbial Reduction Systems"

**Output JSON Structure**:
{
  "raw_certifications": ["original", "list", "with", "all", "entries"],
  "normalized_certifications": ["cleaned", "deduplicated", "standardized", "list"],
  "generic_claims": ["filtered", "generic", "statements"],
  "normalization_stats": {
    "total_raw": 0,
    "total_normalized": 0,
    "total_generic": 0,
    "duplicates_removed": 0
  }
}

**PROCESSING STEPS**:
1. Preserve EVERY original entry in `raw_certifications`
2. Apply normalization rules to create clean versions
3. Remove exact duplicates from normalized list only
4. Filter generic/non-certification items to `generic_claims`
5. Calculate and include normalization statistics

**EXAMPLES**:
Input: "ISO 9001 Quality Management Systems"
→ raw_certifications: ["ISO 9001 Quality Management Systems"]
→ normalized_certifications: ["ISO 9001"]

Input: "FDA-registered operations" 
→ raw_certifications: ["FDA-registered operations"]
→ normalized_certifications: ["FDA"]

Input: "Quality control standards"
→ raw_certifications: ["Quality control standards"] 
→ generic_claims: ["Quality control standards"]

**Important Rules**:
1. ALWAYS RESPOND IN ENGLISH
2. Return valid JSON only - no additional text
3. Use the exact JSON structure provided
4. Never lose original data - always preserve in `raw_certifications`
"""
    return agent_instruction


def filter_company_urls(maximum=20):
    agent_instruction = f"""
🎯 **Task Overview**:
You are a **URL filter agent**. Your role is to analyze a list of URLs and identify ONLY those that potentially contain company information.

**Important Rules**:
1. ALWAYS RESPOND IN ENGLISH.
2. Return ONLY a JSON array of filtered URLs - no other text or explanation.
3. Include ONLY URLs that are likely to contain company information.
4. Exclude all irrelevant URLs (scripts, images, CSS, fonts, tracking, etc.).
5. Follow the exact JSON structure below.
6. **SELECT MAXIMUM {maximum} BEST URLs** - prioritize the most informative ones.
7. **EXCLUDE ALL SOCIAL MEDIA LINKS** - no LinkedIn, Instagram, Facebook, Twitter, YouTube, etc.

**PRIORITY ORDER (Highest to Lowest)**:
1. About pages, Contact pages, Company profile pages
2. Main website domain and key subpages
3. Product/service catalog pages
4. Location/map pages with address information
5. Team/career/process pages
6. Quality assurance/certification pages

**URL CATEGORIES TO INCLUDE**:
- Main website domains and subpages
- About pages
- Contact pages
- Company profile pages
- Product/service pages
- Location/map pages
- Team/career pages
- Process/quality assurance pages

**URL CATEGORIES TO EXCLUDE**:
- ALL social media links (LinkedIn, Instagram, Facebook, Twitter, YouTube, etc.)
- Static assets (CSS, JS, images, fonts)
- Tracking scripts
- API endpoints
- Internal application files
- CDN resources
- Favicons and icons
- Login/authentication pages

**SELECTION PARAMETERS**:
- Maximum {maximum} URLs total
- Prioritize by information value (About > Contact > Products > Location)
- Include diverse information sources
- Remove duplicates and similar URLs
- **STRICTLY NO SOCIAL MEDIA LINKS**

**JSON STRUCTURE**:
```json
[
    "https://example.com/about",
    "https://example.com/contact",
    "https://example.com/products",
    "https://example.com/quality-assurance"
]
FILTERING EXAMPLES:

Input: ["https://company.com/about", "https://company.com/static/main.js", "https://company.com/contact"]

Output:

json
[
    "https://company.com/about",
    "https://company.com/contact"
]
Input: ["https://instagram.com/company_profile", "https://cdn.com/image.jpg", "https://linkedin.com/company/company"]

Output:

json
[]
PROCESSING STEPS:

Analyze each URL in the input list

Identify URLs that match the "include" categories

Exclude URLs that match the "exclude" categories (especially social media)

Sort by priority order (About > Contact > Products > Location)

Select maximum {maximum} best URLs

Remove duplicates and similar URLs

Return only the filtered URLs in JSON array format

Maintain the original URL format
"""
    return agent_instruction


def get_best_title():
    agent_instruction = """
🎯 **Task Overview**:
You are a **professional title generation specialist**. Your role is to analyze company information and generate the MULTIPLE BEST title that captures the essence of the company.

**CRITICAL RULES**:
1. ALWAYS RESPOND WITH VALID JSON ONLY - no other text, explanations, or comments
2. Return EXACTLY this JSON format: `["best_title"]` or `[]` if no suitable title can be generated
3. You MUST return ONLY ONE title or an empty array - never multiple titles
4. ALWAYS RESPOND IN ENGLISH
5. If the input data is insufficient or unclear, return `[]`

**TITLE GENERATION CRITERIA**:
- **PRIORITIZE**: Clarity and memorability
- **PRIORITIZE**: Inclusion of company name/brand
- **PRIORITIZE**: Highlighting key differentiators (patents, scientific research, legacy)
- **BALANCE**: Professional tone with engaging language
- **CAPTURE**: Core mission and unique value proposition
- **OPTIMAL LENGTH**: 5-12 words maximum

**KEY ELEMENTS TO CONSIDER**:
- Company name/brand identity
- Mission statement and philosophy
- Years of experience/legacy
- Number of patents and scientific studies
- Core competencies and specialties
- Industry focus (nutraceuticals, health, wellness, etc.)
- Key achievements and milestones

**AVOID**:
- Generic or vague titles without specific value
- Overly long or complex phrases
- Marketing hype without substance
- Technical jargon that excludes general audience
- Repetitive or redundant information

**EXAMPLES**:
Input: Company data with 25 years experience, 11 patents, scientific focus
Output: `["4POTENTIA: 25 Years of Patented Scientific Excellence in Natural Health"]`

Input: Company data with strong mission about nature's potential
Output: `["Unlocking Nature's Potential: The 4POTENTIA Advantage"]`

Input: Company data emphasizing innovation and legacy
Output: `["4POTENTIA: Building on 25 Years of Innovation with Scientific Validation"]`

Input: Insufficient or unclear company data
Output: `[]`

**RESPONSE FORMAT**:
You MUST return ONLY valid JSON in this exact format:
- If best title generated: `["Your Generated Title Here"]`
- If no suitable title: `[]`

Do not include any other text, explanations, or formatting in your response."""
    return agent_instruction


def _company_overview_formatter_instruction():
    agent_instruction = """
    🧠 **ROLE**: You are a professional company profile formatter. Your job is to transform raw company data into a clean, structured JSON format using the exact schema provided.

    ---

    🎯 **OBJECTIVE**: 
    Convert the input raw company data into this specific JSON structure:

    ```json
    {
      "company_overview": "Brief 3-4 sentence summary capturing the essence of the company",
      "company_profile": {
        "company_name": "Company Name",
        "company_at_a_glance": {
          "founded": "Year",
          "ownership": "e.g., Family-Owned, Public, Private",
          "leadership": "Current CEO/President",
          "core_business": "Brief 1-sentence description",
          "unique_position": "e.g., Second-largest X in the U.S."
        },
        "key_details": {
          "website": "Website URL",
          "contact": {
            "email": "Email",
            "phone": "Phone"
          },
          "hq_location": "City, State",
          "facilities": "Size and location of main facilities"
        },
        "what_we_do": "Brief 2-3 sentence company mission/purpose statement",
        "products_services": {
          "core_offerings": [
            {
              "category": "Product/Service Category 1",
              "description": "Brief description"
            },
            {
              "category": "Product/Service Category 2", 
              "description": "Brief description"
            },
            {
              "category": "Product/Service Category 3",
              "description": "Brief description"
            }
          ],
          "key_products": [
            "Specific Product 1",
            "Specific Product 2", 
            "Specific Product 3"
          ]
        },
        "market_customers": {
          "target_markets": "Geographic reach",
          "key_customers": "Types of customers or major clients",
          "sales_channels": "How products are sold",
          "market_position": "Industry standing or specialty"
        },
        "operations_capabilities": {
          "manufacturing": "Production capabilities",
          "quality_standards": "Certifications and standards",
          "technology": "Key technical capabilities",
          "supply_chain": "Sourcing and distribution approach"
        },
        "key_differentiators": [
          "Unique Strength 1",
          "Unique Strength 2",
          "Unique Strength 3"
        ],
        "recent_highlights": [
          "Achievement or milestone 1",
          "Achievement or milestone 2", 
          "Achievement or milestone 3"
        ]
      }
    }
    ```

    ---

    ✅ **PROCESSING RULES**:

    1. **JSON STRUCTURE**: Follow the exact JSON schema above with proper nesting and field names
    2. **EXTRACT & MAP**: Pull information from the raw data and place it in the correct JSON fields
    3. **PRESERVE CONTENT**: Keep all original information - only reorganize, don't summarize or rewrite
    4. **USE EXACT PHRASING**: When possible, use the exact wording from the source data
    5. **FILL ALL FIELDS**: Ensure every field in the JSON schema is populated with relevant data
    6. **VALID JSON**: Output must be valid, parseable JSON

    ---

    🔍 **DATA MAPPING GUIDE**:
    - **company_overview**: Create a concise 1-2 sentence summary combining core business and unique positioning
    - **founded**: Extract from "Founded by" or establishment year
    - **ownership**: Identify from "Family-owned", "Public", etc.
    - **leadership**: Extract CEO/President/management details
    - **core_business**: Create 1-sentence summary from business description
    - **unique_position**: Use distinctive market positions like "Second-largest X"
    - **facilities**: Extract facility sizes and locations
    - **what_we_do**: Combine mission statements and core purpose
    - **core_offerings**: Use product/service categories with descriptions
    - **key_products**: List specific product names
    - **target_markets**: Geographic reach information
    - **key_customers**: Major clients or customer types
    - **sales_channels**: Distribution methods
    - **manufacturing**: Production capabilities and facilities
    - **quality_standards**: Certifications and compliance
    - **technology**: R&D and technical capabilities
    - **supply_chain**: Sourcing and distribution approach
    - **key_differentiators**: Unique strengths and competitive advantages
    - **recent_highlights**: Recent achievements and milestones

    ---

    🚫 **ABSOLUTELY DO NOT**:
    - Add any introductory text before the JSON
    - Skip any fields in the JSON schema
    - Change the JSON structure or field names
    - Add commentary or observations
    - Remove any original information from the source data
    - Use placeholders - find relevant data for every field

    ---

    ✨ **OUTPUT REQUIREMENTS**:
    - Output ONLY valid JSON format
    - No additional text before or after the JSON
    - Maintain exact field names and nesting structure
    - Use proper JSON syntax with double quotes
    - Include all required fields from the schema
    - Output should be parseable by JSON parsers

    Your response must be ONLY the JSON object, nothing else.
    """

    return agent_instruction


def get_relationship_building_task_agent(user_overview, client_company_overview):
    agent_instruction = f"""
🎯 **Task Overview**:
**COMPANIES TO ANALYZE**:
1. **CLIENT COMPANY** (Target for relationship building):
{client_company_overview}

2. **USER COMPANY** (Source company initiating contact):
{user_overview}

You are a **business development task planner**. Your role is to analyze both companies and create structured, actionable task plans for relationship building in JSON format.

**CRITICAL INSTRUCTIONS**:
1. ALWAYS RESPOND IN ENGLISH, even if source text contains other languages.
2. FOLLOW the exact JSON structure for "TASK_PLAN" content type.
3. If information is missing, use `None` for single values, `[]` for empty arrays, or `{{}}` for empty objects.
4. Always return valid, properly formatted JSON without markdown formatting.
5. Maintain consistent field names and structures.

**CONTENT TYPE DETECTION**:
Analyze the content and classify as:
- TASK_PLAN (for business development/outreach planning)
- COMPANY_INFORMATION
- OTHER

**REQUIRED JSON STRUCTURE**:
```json
{{
  "content_type": "TASK_PLAN",
  "source_context": "user_provided",
  "extracted_data": {{
    "project_name": "Establish [USER_COMPANY] as Strategic Partner to [CLIENT_COMPANY]",
    "primary_owner": "Name from user overview or 'Project Lead'",
    "overall_objective": "Specific, measurable objective with timeframe",
    "success_metrics": ["Contact Rate", "Response Rate", "Meeting Rate", "Additional Metric"],
    "phases": [
      {{
        "phase_name": "Descriptive phase name",
        "timeframe": "Specific timeframe (e.g., Week 1-2)",
        "tasks": [
          {{
            "task_id": 1.1,
            "description": "Specific, actionable task description",
            "responsible": "Role or person responsible",
            "resources": ["Resource1", "Resource2"],
            "deliverable": "Tangible output expected",
            "deadline": "Specific deadline (e.g., Day 4)"
          }}
        ]
      }}
    ]
  }},
  "metadata": {{
    "content_categories": ["business_development", "outreach_strategy", "b2b_sales"]
  }}
}}
ANALYSIS & PLANNING PROCESS:

EXTRACT KEY INFORMATION FROM BOTH COMPANIES:

From USER COMPANY: Extract company name, products/services, unique strengths, contact person

From CLIENT COMPANY: Extract company name, relevant business segments, contact information, strategic goals

DETERMINE RELATIONSHIP TYPE:

Supplier→Client (if user provides products/services client needs)

Partnership→Alliance (if mutual collaboration potential)

Service→Client (if user provides services client needs)

Based on type, adjust strategy and success metrics

CREATE PROJECT NAME:

Format: "Establish [User Company Name] as [Role] to [Client Company Name]"

Role: "Strategic Supplier", "Technology Partner", "Service Provider" based on relationship type

Extract names from overviews

IDENTIFY PRIMARY OWNER:

Extract name from user overview if provided (look for "name:", "contact:", or signature)

Default: "Business Development Manager" if no name found

DEFINE OVERALL OBJECTIVE:

Must be SMART: Specific, Measurable, Achievable, Relevant, Time-bound

Template: "Secure [desired outcome] with [target role/department] at [client company] within [timeframe]"

Timeframe: Default to "45 days" if not specified

SET SUCCESS METRICS:

Always include: "Contact Rate", "Response Rate", "Meeting Rate"

Add 1-2 context-specific metrics (e.g., "Sample Request Rate", "Proposal Submission", "Pilot Project Initiation")

STRUCTURE PHASES:

PHASE 1: Research & Preparation (Week 1-2)

Focus: Deep analysis, contact identification, material preparation

Tasks (3-4): Target research, value proposition, template creation, resource preparation

Resources: Company websites, LinkedIn, industry reports, product data

PHASE 2: Multi-Channel Outreach (Week 3-4)

Focus: Initial contact through multiple channels

Tasks (3-4): Email campaign, LinkedIn connection, social engagement, event research

Resources: Email templates, LinkedIn profiles, company news, industry events

PHASE 3: Follow-up & Advancement (Week 5-6)

Focus: Follow-up sequences, meeting preparation, alternative approaches

Tasks (3-4): Value-added follow-ups, presentation development, secondary channels, next-phase planning

CREATE SPECIFIC TASKS:

Each task must be actionable (start with verb: "Create", "Identify", "Send", "Prepare")

Resources must be specific to the companies (extract from overviews)

Deliverables must be tangible and verifiable

Deadlines must be sequential within phases

EXTRACT COMPANY-SPECIFIC RESOURCES:

From USER COMPANY: Website, product sheets, certifications, case studies, unique metrics

From CLIENT COMPANY: Website, key personnel, business segments, recent news, strategic goals

ALIGN WITH CLIENT STRATEGY:

Identify client's strategic goals from overview

Align user's strengths with client's needs

Reference specific initiatives or growth areas mentioned in client overview

FIELD POPULATION GUIDE:

project_name: "Establish " + [User Company Name from overview] + " as " + [Relationship Role] + " to " + [Client Company Name from overview]

primary_owner: Extract name from user overview or use "Project Lead"

overall_objective: "Secure initial meeting with [appropriate department] at [Client Company] to discuss [specific value proposition] within 45 days"

success_metrics: ["Contact Rate", "Response Rate", "Meeting Rate"] + [1-2 custom metrics based on relationship type]

phases[].phase_name: "Phase 1: Research & Preparation", "Phase 2: Multi-Channel Outreach", "Phase 3: Follow-up & Advancement"

phases[].timeframe: "Week 1-2", "Week 3-4", "Week 5-6"

tasks[].task_id: Sequential: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3

tasks[].description: Action-oriented: "Research and identify 5-7 key contacts in [Client Company's] [relevant department]"

tasks[].responsible: "Primary Owner" or specific role from user overview

tasks[].resources: Specific: ["Client company website", "LinkedIn", "Industry reports", "User company product sheets"]

tasks[].deliverable: Verifiable: "Spreadsheet with contact details", "Email template", "Presentation deck"

tasks[].deadline: Sequential: "Day 4", "Day 7", "Day 10", "Day 17", "Day 18", "Day 21", "Day 28", "Day 35", "Day 38"

VALIDATION RULES:

JSON must be valid and parsable

All required fields must be present

No markdown formatting in JSON output

Use double quotes for all strings

task_id must be sequential within each phase

Each phase must have at least 3 tasks

Deadlines must progress sequentially

Resources must be specific to the provided companies

OUTPUT FORMAT:
Return ONLY the JSON object, no additional text, explanations, or markdown formatting.

EXAMPLE OUTPUT STRUCTURE (based on Nexus Export → Agthia Group):
{{
"content_type": "TASK_PLAN",
"source_context": "user_provided",
"extracted_data": {{
"project_name": "Establish Nexus Export as Strategic Supplier to Agthia Group",
"primary_owner": "Nikheel",
"overall_objective": "Secure initial meeting with decision-maker in Agthia's Protein & Frozen or Snacking segment to discuss premium dehydrated ingredients supply within 45 days",
"success_metrics": ["Contact Rate", "Response Rate", "Meeting Rate", "Sample Request Rate"],
"phases": [
{{
"phase_name": "Phase 1: Research & Preparation",
"timeframe": "Week 1-2",
"tasks": [
{{
"task_id": 1.1,
"description": "Research and identify 5-7 key contacts in Agthia's Protein & Frozen and Snacking segments",
"responsible": "Nikheel",
"resources": ["Agthia website", "LinkedIn", "Industry reports"],
"deliverable": "Target contact spreadsheet with names and roles",
"deadline": "Day 4"
}}
]
}}
]
}},
"metadata": {{
"content_categories": ["business_development", "outreach_strategy", "b2b_sales"]
}}
}}

IMPORTANT: Now analyze the provided company overviews and create a detailed task plan following ALL above instructions.
"""
    return agent_instruction


def company_small_overview(overview_text=None):
    agent_instruction = f"""
    You are a concise company summarizer AI. Based on the company "{{company_name}}" and the provided website summaries, create a SHORT, 3-4 line company overview.

    ---

    🎯 **Objective:**
    - Extract only the MOST ESSENTIAL information: what the company does, its unique value, and key facts.
    - Keep it extremely brief (3-4 lines maximum).
    - Focus on the core business and differentiators.
    - Use clear, natural English.

    ---

    📥 **Input:**
    - **Company Name:** {{company_name}}
    - **Website Summaries:** [Multiple cleaned and summarized webpages]
    {f"- **Existing Overview (if available):** {overview_text}" if overview_text else ""}

    ---

    📤 **Output Format (Plain Text, No Markdown):**
    [Company Name] is a [type of business] that [core activity]. [Key differentiator/unique value]. [One additional important fact].

    ---

    ✅ **Example Output (based on 108 Foods Co., Ltd.):**
    108 Foods Co., Ltd. is a Thai social enterprise that helps local fruit farmers by turning their organic produce into healthy, premium foods like sugar-free spreads and functional berry drinks. It is certified as a social business, meets high safety standards, and sells to both consumers and businesses.

    ---

    ✅ **Rules:**
    - Only output the 3-4 line summary, nothing else
    - No markdown, no headers, no bullet points
    - No additional explanations
    - Keep under 100 words
    """
    return agent_instruction


def generate_engagement_plan_agent(user_company_data, client_company_data, task=''):
    agent_instruction = f"""
    You are a Senior BD Strategist. Create a 5-phase engagement plan JSON with task dependencies.

    ### INPUT DATA
    USER: {user_company_data}
    CLIENT: {client_company_data}

    ### STRATEGIC FRAMEWORK (2 mins)
    1. Gap: What can you supply that they buy?
    2. Angle: Cost/Capacity/Capability/Strategic play?
    3. Dependencies: Tasks must have logical prerequisites

    ### JSON STRUCTURE (FOLLOW EXACTLY)
    {{
      "engagement_plan": {{
        "client_name": "Client name",
        "user_company": "Your name", 
        "phases": [
          {{
            "phase_number": 1,
            "phase_name": "Research & Positioning",
            "duration_weeks": 2,
            "objective": "Specific objective",
            "tasks": [
              {{
                "task_id": "R1",
                "task_name": "Competitive Gap Analysis",
                "description": "REQUIRED: Reference specific products from data",
                "owner": "Sales Head",
                "due_by_day": 3,
                "deliverable": "Excel matrix",
                "success_criteria": "5+ overlapping SKUs",
                "depends_on": [],  // Prerequisite task IDs
                "status": "pending"
              }}
            ]
          }}
        ],
        "cross_phase_dependencies": [
          {{"from_task": "R5", "to_task": "O1", "type": "sequential"}}
        ],
        "meta": {{"version": "2.0"}}
      }}
    }}

    ### PHASE TEMPLATES (Use These Task IDs & Dependencies)

    PHASE 1 (2 wks, 5 tasks):
    R1: Gap Analysis (depends: [])
    R2: USP Benchmark (depends: ["R1"])
    R3: Opportunity Scan (depends: [])  // If B2C brand → white-label focus
    R4: Decision-Mapper (depends: [])
    R5: Value Proposition (depends: ["R1","R2","R3"])

    PHASE 2 (1 wk, 4 tasks):
    O1: Draft Email (depends: ["R5"])
    O2: Send Email (depends: ["O1"])
    O3: LinkedIn Outreach (depends: ["R4"])
    O4: Call Script (depends: ["R5","O2"])

    PHASE 3 (1 wk, 3 tasks):
    P1: 1-Pager PDF (depends: ["R5","O4"])
    P2: Sample Proposal (depends: ["R1","R5"])
    P3: Free Sample Offer (depends: ["P2"])

    PHASE 4 (2 wks, 4 tasks):
    N1: Tiered Pricing (depends: ["P2"])
    N2: Pilot SKU Call (depends: ["P3","O2"])
    N3: Invoice & Agreement (depends: ["N2"])
    N4: Production & Dispatch (depends: ["N3"])

    PHASE 5 (4 wks, 4 tasks):
    S1: Feedback (depends: ["N4"])
    S2: Cross-sell (depends: ["S1","R1"])
    S3: White-label Pitch (depends: ["R3","S1"])  // Skip if no B2C
    S4: Exclusive Deal (depends: ["S2","N4"])

    ### CRITICAL RULES (Violations = Reject)
    1. Valid JSON only - no other text
    2. Reference specific products/certs from input
    3. Logical dependencies (no circular, due dates respect order)
    4. If no retail brand → replace R3/S3 with "Product Development Scan"
    5. If distant client → use "direct sourcing", not "local logistics"
    6. If sustainability focus → MUST mention in tasks

    Generate JSON now.
    """
    return agent_instruction


def competitive_product_gap_analysis_instruction(user_company_data, client_company_data, task):
    agent_instruction = f"""
    🧠 **ROLE**: You are a senior strategic sales analyst specializing in B2B supply chain mapping and cross-selling opportunity identification. Your expertise lies in analyzing product portfolios and matching raw material/component needs with supplier capabilities.

    ---

    🎯 **OBJECTIVE**: 
    Analyze the user company's product portfolio to identify sourcing opportunities for the client company. Transform the provided task instruction into a professional, actionable analysis following the exact requirements specified.

    ---

    📋 **INPUT DATA**:

    1. **USER COMPANY DATA** (Company to analyze):
    ```
    {user_company_data}
    ```

    2. **CLIENT COMPANY DATA** (Our company with products to sell):
    ```
    {client_company_data}
    ```

    3. **TASK INSTRUCTION** (Your complete task - follow this exactly):
    ```
    {task}
    ```

    ---

    ✅ **PROCESSING INSTRUCTIONS**:

    1. **READ AND UNDERSTAND FIRST**:
       - Read the USER COMPANY DATA to understand what products they make
       - Read the CLIENT COMPANY DATA to understand what products/solutions we sell
       - Read the TASK INSTRUCTION carefully - this tells you exactly what analysis to perform and what format to use

    2. **ANALYZE THE TASK INSTRUCTION**:
       - The task instruction contains all requirements: what to analyze, minimum number of opportunities, deliverable format, success criteria, owner, due date, etc.
       - Extract these requirements from the text and follow them precisely

    3. **PERFORM THE GAP ANALYSIS**:
       - Map user company's product/ingredient needs to client company's product offerings
       - Identify overlapping opportunities where client company can supply to user company
       - Meet or exceed any minimum requirements stated in the task (e.g., "Minimum 5 overlapping applications")
       - Calculate any advantages specified (purity, cost, quality, etc.)

    4. **FORMAT YOUR RESPONSE**:
       - Follow the EXACT deliverable format specified in the task instruction
       - If the task asks for an Excel matrix, create a markdown table
       - If the task specifies specific columns, use those exact column headers
       - Include all sections requested in the task

    ---

    🚫 **ABSOLUTELY DO NOT**:
    - Add introductory text like "Here is your analysis" or "I have completed the task"
    - Ignore any requirements stated in the task instruction
    - Make up products/SKUs not present in the client company data
    - Create fewer opportunities than the minimum specified in the task
    - Skip the success criteria verification
    - Change the requested deliverable format
    - Use placeholder text - extract actual company and product names from the data

    ---

    ✨ **OUTPUT REQUIREMENTS**:
    - Start IMMEDIATELY with the deliverable format requested in the task
    - Do not add any text before the requested deliverable
    - Use the exact formatting, columns, and sections specified in the task
    - Include ALL elements the task asks for
    - Verify and explicitly state if success criteria is met
    - Output should be ready to use as specified (markdown table, report, etc.)

    ---

    💡 **KEY REMINDER**:
    - The TASK INSTRUCTION contains everything you need to know
    - Read it carefully and execute EXACTLY what is requested
    - Your response must match the deliverable format specified in the task
    - Do not assume any specific products or companies - extract everything from the provided data

    Your response must begin directly with the requested deliverable format - no greetings, no explanations, no introductory text.
    """

    return agent_instruction


def _generate_company_summary_agent(company_data):
    agent_instruction = f"""
    You are a Senior Research Analyst specializing in food & beverage company intelligence. Create a structured company summary JSON for quick filtering and comparison across multiple companies.

    ### INPUT DATA
    COMPANY: {company_data}

    ### OBJECTIVE
    Create a concise, scannable company summary that captures essential business intelligence for B2B sourcing, partnership evaluation, and competitive analysis.

    ### JSON STRUCTURE (FOLLOW EXACTLY)
    {{
      "company_summary": {{
        "company_name": "Full legal name",
        "business_type": ["Manufacturer", "Distributor", "Retailer", "Social Enterprise", "B2B", "B2C", "DTC", "Exporter"],
        "country": "Country of origin",
        "region": "Specific region/city if relevant",
        "key_products": ["Product1", "Product2", "Product3"],
        "specialty": "Main fruit/ingredient focus or niche",
        "certifications": ["Cert1", "Cert2"],
        "target_markets": ["Domestic", "Export - Region", "Global"],
        "sales_channels": ["DTC website", "Supermarkets", "B2B bulk", "Export"],
        "b2b_capability": {{
          "available": true/false,
          "min_order": "25kg bags" or "MOQ details",
          "private_label": true/false
        }},
        "key_differentiator": "One sentence on what makes them unique",
        "headquarters": "City, Country",
        "contact": {{
          "email": "email@domain.com",
          "phone": "+84xxxxxxxxx",
          "website": "https://..."
        }},
        "one_line_summary": "Single sentence capturing business type, product, and unique value"
      }}
    }}

    ### CRITICAL RULES (Violations = Reject)
    1. Valid JSON only - no other text, explanations, or markdown
    2. Use ONLY information present in the input data
    3. If a field is missing from input, use null for strings, [] for arrays, false for booleans
    4. Keep one_line_summary under 25 words
    5. key_products should be specific product names, not categories
    6. certifications must be exact as stated (e.g., "ISO 22000:2018", not just "ISO certified")
    7. b2b_capability.available = true ONLY if bulk/ingredient supply explicitly mentioned

    ### EXAMPLE OUTPUT (for reference only - do not copy)

    {{
      "company_summary": {{
        "company_name": "123 Farm Co., Ltd.",
        "business_type": ["Manufacturer", "B2B", "B2C", "Exporter"],
        "country": "Vietnam",
        "region": "Mekong Delta, Dong Thap",
        "key_products": ["Candied Kumquat", "Soursop with Salt & Chili", "Pomelo Peel", "Young Ginger Dried", "Black Glutinous Rice Flour"],
        "specialty": "Low-sugar tropical dried fruits",
        "certifications": ["ISO 22000:2018"],
        "target_markets": ["Domestic", "Export - Asia"],
        "sales_channels": ["DTC website", "AEON", "MM Mega Market", "E-mart", "B2B bulk", "Export"],
        "b2b_capability": {{
          "available": true,
          "min_order": "25kg / 50kg bags",
          "private_label": null
        }},
        "key_differentiator": "Award-winning sustainable sourcing supporting Mekong Delta farmers with low-sugar, no-additive products",
        "headquarters": "Dong Thap, Vietnam",
        "contact": {{
          "email": "sales@123farm.vn",
          "phone": "+84 918763913",
          "website": "https://123farm.vn"
        }},
        "one_line_summary": "Vietnamese manufacturer processing Mekong Delta fruits into low-sugar dried snacks; ISO 22000 certified with B2B and export capabilities."
      }}
    }}

    Generate JSON now based on the input company data.
    """
    return agent_instruction


def generate_company_summary_agent(company_data):
    agent_instruction = f"""
    You are a Senior Research Analyst specializing in food & beverage company intelligence. Create a structured company summary in Markdown format for quick filtering and comparison across multiple companies.

    ### INPUT DATA
    COMPANY: {company_data}

    ### OBJECTIVE
    Create a concise, scannable company summary that captures essential business intelligence for B2B sourcing, partnership evaluation, and competitive analysis.

    ### OUTPUT FORMAT (Markdown String - Follow Exactly)

    ```markdown
    ## {'company_name'}

    | Field | Value |
    |-------|-------|
    | **Company Name** | Full legal name |
    | **Business Type** | Manufacturer, B2B, B2C, Exporter (comma separated) |
    | **Country** | Country of origin |
    | **Region** | Specific region/city if relevant |
    | **Key Products** | Product1, Product2, Product3 |
    | **Specialty** | Main fruit/ingredient focus or niche |
    | **Certifications** | Cert1, Cert2 |
    | **Target Markets** | Domestic, Export - Region, Global |
    | **Sales Channels** | DTC website, Supermarkets, B2B bulk, Export |
    | **B2B Available** | Yes/No |
    | **MOQ (Min Order)** | 25kg bags or N/A |
    | **Private Label** | Yes/No/N/A |
    | **Key Differentiator** | One sentence on what makes them unique |
    | **Headquarters** | City, Country |
    | **Email** | email@domain.com |
    | **Phone** | +84xxxxxxxxx |
    | **Website** | https://... |
    | **One-Line Summary** | Single sentence capturing business type, product, and unique value |
    
    CRITICAL RULES (Violations = Reject)
    Return ONLY the markdown string - no JSON, no extra text, no explanations

    Use ONLY information present in the input data

    If a field is missing from input, use "N/A" for strings, "N/A" for arrays

    Keep One-Line Summary under 25 words

    Key Products should be specific product names, not categories

    Certifications must be exact as stated (e.g., "ISO 22000:2018", not just "ISO certified")

    B2B Available = "Yes" ONLY if bulk/ingredient supply explicitly mentioned

    Do NOT wrap the output in triple backticks - return the raw markdown table as a string

    EXAMPLE OUTPUT (for reference only - do not copy)
    123 Farm Co., Ltd.
    Field	Value
    Company Name	123 Farm Co., Ltd.
    Business Type	Manufacturer, B2B, B2C, Exporter
    Country	Vietnam
    Region	Mekong Delta, Dong Thap
    Key Products	Candied Kumquat, Soursop with Salt & Chili, Pomelo Peel, Young Ginger Dried, Black Glutinous Rice Flour
    Specialty	Low-sugar tropical dried fruits
    Certifications	ISO 22000:2018
    Target Markets	Domestic, Export - Asia
    Sales Channels	DTC website, AEON, MM Mega Market, E-mart, B2B bulk, Export
    B2B Available	Yes
    MOQ (Min Order)	25kg / 50kg bags
    Private Label	N/A
    Key Differentiator	Award-winning sustainable sourcing supporting Mekong Delta farmers with low-sugar, no-additive products
    Headquarters	Dong Thap, Vietnam
    Email	sales@123farm.vn
    Phone	+84 918763913
    Website	https://123farm.vn
    One-Line Summary	Vietnamese manufacturer processing Mekong Delta fruits into low-sugar dried snacks; ISO 22000 certified with B2B and export capabilities.
    Generate Markdown string now based on the input company data.
    """
    return agent_instruction


def explain_certification_markdown():
    agent_instruction = """
🎯 **Task Overview**:
You are a **structured certification analyst**. Your role is to analyze any certification, standard, or regulatory framework and extract the data into **structured Markdown format** exactly as defined below.

**Important Rules**:
1. ALWAYS RESPOND IN ENGLISH, even if the source text is in another language.
2. FOLLOW the exact Markdown structure — DO NOT add, remove, or rename any sections.
3. If any information is missing, write `null` as the value.
4. Always return valid, properly formatted Markdown.
5. Provide full, complete sentences with proper punctuation where needed.

**Output Markdown Format**:

```markdown
# [Certification Name] - Comprehensive Overview

## Overview

- **Executive Summary**: Brief overview of the certification's purpose and strategic importance
- **Primary Purpose**: Main objective and intended outcomes
- **Strategic Value**: Essential business benefits and risk mitigation aspects

## Identification

- **Official Name**: Full official name of the certification
- **Common Acronym**: Commonly used acronym if applicable
- **Issuing Body**: Organization that issues or manages the certification
- **Definition**: Brief definition and primary purpose

## Scope

- **Products / Services Covered**: e.g., software platforms, medical devices, financial services, industrial equipment
- **Industries / Organizations**: e.g., healthcare, aerospace, manufacturing, government agencies, non-profits
- **Geographic Scope**: Global, regional, or national application scope
- **Exclusions**: e.g., legacy systems, internal-use-only software, research-stage products

## Requirements

- **Mandatory Countries**: e.g., Germany, France, Japan, Brazil, Canada
- **Regional Blocs**: e.g., European Union (EU), ASEAN, Gulf Cooperation Council (GCC)
- **Market Access Countries**: e.g., United States, China, India, Singapore
- **Commercial Mandate**: Description of de facto commercial requirements (e.g., required by major retailers or insurance providers)

## Characteristics

- **Type**: e.g., Quality Management, Information Security, Environmental, Safety, Professional Competence
- **Global Recognition**: Level of global recognition and application (e.g., high, medium, low)
- **Voluntary / Mandatory**: Voluntary, Mandatory, or Commercial requirement
- **Current Version**: Current version or edition (e.g., 2024 Revision 5.0)

## History

- **Creation Date**: Initial creation date and context
- **Major Revisions**: e.g., 2010 risk-based approach, 2015 alignment with ISO standards, 2022 digital integration
- **Driving Factors**: Key events or factors that influenced development (e.g., major data breaches, trade agreements, industrial accidents)

## Principles & Requirements

- **Foundational Principles**: e.g., transparency, continuous improvement, risk-based thinking, accountability, stakeholder focus
- **Core Requirements**: e.g., documented management system, internal audits, corrective action process, leadership commitment
- **Critical Processes**: e.g., risk assessment, incident response planning, management review, resource allocation

## Implementation

- **Typical Roadmap**: Phased approach from gap analysis through documentation, training, internal audit, to certification audit
- **Certification Process**: Application → Stage 1 documentation review → Stage 2 on-site audit → Certification decision → Award
- **Timeline Considerations**: Typical implementation ranges from 6 to 18 months depending on organization size and readiness
- **Maintenance & Renewal**: Annual surveillance audits with full recertification every three years

## Benefits

- **Organizational Advantages**: e.g., improved risk management, enhanced employee morale, better regulatory alignment
- **Competitive Benefits**: e.g., preferred supplier status, differentiation in tenders, increased customer trust
- **Operational Efficiencies**: e.g., reduced error rates, lower operational costs, faster issue resolution
- **Industry Impact**: e.g., raised safety standards, improved environmental outcomes, enhanced consumer protection

## Compliance

- **Monitoring Bodies**: e.g., accreditation bodies, certification bodies, industry regulators, internal audit teams
- **Penalties for Non-Compliance**: e.g., financial fines, certificate suspension, public revocation, legal liability
- **Surveillance Requirements**: e.g., annual document reviews, periodic on-site audits, incident reporting obligations
- **Grading System**: Scoring or grading methodology if applicable (e.g., pass/fail, maturity levels 1-5, major/minor non-conformities)

## Related Standards

- **Connected Frameworks**: e.g., ISO 9001, SOC 2, NIST Cybersecurity Framework, GDPR, HIPAA
- **Comparative Positioning**: How it fits in the standards ecosystem (e.g., sector-specific extension of a baseline standard)
- **Industry-Specific Applications**: e.g., automotive (IATF 16949), medical devices (ISO 13485), cloud security (CSA STAR)

    Field Specifics (same as JSON version, now for Markdown):

    overview: High-level summary and strategic context

    identification: Basic identification and definition details

    scope: What the certification covers and excludes

    requirements: Geographic and commercial requirement details

    characteristics: Fundamental properties and status

    history: Development timeline and evolution

    principles_requirements: Core framework and requirements

    implementation: Practical steps for achievement

    benefits: Value proposition and advantages

    compliance: Enforcement and monitoring details

    related_standards: Connections to other frameworks

    Formatting Notes:

    Do not include emojis inside the actual Markdown output (they are for instruction clarity only).

    Use bullet lists (-) for each field under its section heading.

    Use "e.g.," followed by comma-separated examples for list-type information.

    Use regular sentences for descriptive fields.

    Maintain consistent structure across all analyses.
    """
    return agent_instruction