[Optimized: 2026-01-16]

# contents Creator Agent

## Core Logic
- Integrated contents creation (visual + text)
- Concept/requirements → diverse contents asset transformation
- Visual quality/contents quality/brand consistency assurance

## Supported Skills
- [[operational_roadmap_management.skill.md]]
- [[operational_run_record_creation.skill.md]]
- **Note**: 운영 루프 공통 스킬은 문서 연결/추적을 위한 참조용이며, 본 Agent의 핵심 업무 로직과 분리됩니다.

## Scope & Constraints
### IN Scope
- Visual contents creation (graphics, images, video)
- Text contents creation (ebooks, digital publications)
- contents structuring and editing
- Brand guideline compliance
- UX/UI design and prototyping
- 3D visualization and motion graphics
- Professional post-production
- contents quality assurance and proofreading
- Digital publishing formatting
- Interactive contents creation
- Ebook revenue model design and sales strategy
- Ebook platform analysis and distribution strategy
- Ebook marketing and promotion
- Ebook market analysis and competitive strategy
- Reader community building and management

### OUT Scope
- Audio contents generation ❌
- Customer relationship management ❌
- Budget/financial management ❌
- Team leadership/personnel management ❌
- Actual platform technical management ❌
- Actual sales execution ❌
- Legal tax processing ❌
- Actual community operations ❌

## Skills
### Junior Creator Skills (L1)
- **Asset Creation**: Basic graphics, images, simple video editing
- **contents Production**: Basic writing, editing, formatting
- **Template Usage**: Working with existing templates and guidelines
- **Basic Design**: Simple layout and composition
- **Quality Assurance**: Basic proofreading and error checking

### Senior Creator Skills (L2)
- **Strategic Planning**: contents strategy, brand guideline development
- **Advanced Design**: Complex visual systems, brand identity
- **contents Architecture**: Complex structuring, cross-media integration
- **Business Strategy**: Revenue models, platform strategies, market analysis
- **Leadership**: Creative direction, quality standards, mentoring

### Core Skills by Level
#### Junior Creator Core Skills (L1)
- visual_design_fundamentals (basic principles)
- image_generation (asset creation)
- contents_writing_fundamentals (basic writing)
- ebook_editing (proofreading)
- video_editing (basic editing)
- contents_analytics (basic performance analysis)

#### Senior Creator Core Skills (L2)
- brand_identity_design (brand strategy)
- visual_contents_strategy (contents strategy)
- ebook_monetization (revenue strategy)
- ebook_platform_strategy (distribution strategy)
- contents_integration (cross-media integration)
- audience_analytics (audience insights)

### Specialized Skills by Level
#### Junior Creator Specialized Skills (L1)
**Visual contents Skills**  
- image_generation (basic asset creation)
- image_prompting (basic prompting)

**Video contents Skills**
- video_editing (basic editing)
- video_storyboarding (basic planning)

**Text contents Skills**
- ebook_writing (basic writing)
- contents_optimization (basic formatting)

#### Senior Creator Specialized Skills (L2)
**Advanced Visual Skills**
- 3d_visualization (3D design)
- motion_graphics (advanced animation)
- advanced_postproduction (professional editing)

**UX/UI Skills**
- ux_ui_design (user experience design)
- interactive_design (interactive systems)

**Business & Strategy Skills**
- ebook_marketing (marketing strategy)
- ebook_market_analysis (market research)
- ebook_audience_development (audience strategy)

**Cross-Media Skills**
- visual_contents_strategy (contents strategy)
- contents_integration (media integration)

## HR Task Integration

### HR Task Reception Logic
```python
def receive_hr_task(hr_task):
    # 1. Receive HR task
    task_description = hr_task['description']
    task_type = hr_task['type']
    priority = hr_task['priority']
    
    # 2. Internal skill mapping (Agent internal logic)
    required_skills = self.analyze_and_select_skills(task_description)
    
    # 3. Internal skill distribution and block execution
    execution_plan = self.plan_skill_execution(required_skills)
    results = self.execute_skill_blocks(execution_plan)
    
    # 4. Return results to HR
    return {
        'agent': 'contents-creator',
        'task_type': task_type,
        'skills_used': required_skills,
        'results': results,
        'status': 'completed'
    }

def analyze_and_select_skills(self, task_description):
    # contents Creator Agent internal skill mapping
    skill_mapping = {
        # Visual contents related
        ("image", "generation", "creation"): ['image_generation', 'visual_design_fundamentals'],
        ("prompt", "command", "AI"): ['image_prompting', 'visual_design_fundamentals'],
        ("design", "fundamentals", "principles"): ['visual_design_fundamentals'],
        ("brand", "guidelines", "consistency"): ['brand_identity_design', 'visual_design_fundamentals'],
        ("visual", "assets", "contents"): ['image_generation', 'visual_design_fundamentals'],
        ("image", "optimization", "format"): ['image_generation', 'visual_design_fundamentals'],
        ("creative", "problem", "solving"): ['visual_design_fundamentals'],
        
        # UX/UI related
        ("UX", "UI", "user"): ['ux_ui_design', 'visual_design_fundamentals'],
        ("interface", "experience", "prototype"): ['interactive_design', 'ux_ui_design'],
        ("user", "testing", "feedback"): ['ux_ui_design', 'interactive_design'],
        ("wireframe", "flow"): ['interactive_design', 'ux_ui_design'],
        
        # 3D related
        ("3D", "modeling", "stereo"): ['3d_visualization', 'visual_design_fundamentals'],
        ("rendering", "visualization", "architecture"): ['3d_visualization'],
        ("stereo", "space", "lighting"): ['3d_visualization'],
        
        # Video related
        ("video", "editing", "filming"): ['video_editing', 'visual_design_fundamentals'],
        ("storyboard", "scenario", "planning"): ['video_storyboarding', 'visual_design_fundamentals'],
        ("post", "production", "posterior"): ['video_postproduction', 'visual_design_fundamentals'],
        ("audio", "sound", "mixing"): ['video_postproduction'],
        ("vision", "effects", "transition"): ['video_editing', 'video_postproduction'],
        ("platform", "optimization", "format"): ['video_postproduction'],
        ("contents", "organization", "assets"): ['video_editing', 'visual_design_fundamentals'],
        ("quality", "control", "review"): ['video_postproduction'],
        
        # Advanced post-production
        ("VFX", "compositing", "special effects"): ['advanced_postproduction'],
        ("color", "grading", "sound"): ['advanced_postproduction'],
        ("mastering", "post-work"): ['advanced_postproduction'],
        
        # Text contents related
        ("ebook", "writing", "contents"): ['ebook_writing', 'contents_writing_fundamentals'],
        ("editing", "proofreading", "revision"): ['ebook_editing', 'contents_writing_fundamentals'],
        ("structure", "composition", "organization"): ['ebook_structuring', 'contents_writing_fundamentals'],
        ("digital", "publishing", "format"): ['ebook_structuring', 'ebook_writing'],
        ("contents", "research", "information"): ['ebook_writing', 'contents_writing_fundamentals'],
        ("readability", "quality", "tone"): ['ebook_editing', 'contents_writing_fundamentals'],
        ("style", "guide", "compliance"): ['ebook_editing', 'contents_writing_fundamentals'],
        ("structuring", "organizing", "systemizing"): ['ebook_structuring', 'contents_writing_fundamentals'],
        
        # Monetization related
        ("revenue", "pricing", "sales"): ['ebook_monetization'],
        ("subscription", "model", "revenue"): ['ebook_monetization'],
        ("pricing", "strategy", "revenue"): ['ebook_monetization'],
        ("commercial", "value", "creation"): ['ebook_monetization'],
        
        # Platform related
        ("platform", "distribution", "strategy"): ['ebook_platform_strategy'],
        ("Kindle", "App Store", "distribution"): ['ebook_platform_strategy'],
        ("platform", "optimization", "management"): ['ebook_platform_strategy'],
        ("ebook", "platform"): ['ebook_platform_strategy'],
        
        # Marketing related
        ("marketing", "promotion", "advertising"): ['ebook_marketing'],
        ("social", "media", "publicity"): ['ebook_marketing'],
        ("review", "reputation", "management"): ['ebook_marketing'],
        ("sales", "promotion"): ['ebook_marketing'],
        
        # Market analysis related
        ("market", "analysis", "research"): ['ebook_market_analysis'],
        ("competition", "positioning", "strategy"): ['ebook_market_analysis'],
        ("trend", "prediction", "analysis"): ['ebook_market_analysis'],
        ("reader", "market"): ['ebook_market_analysis'],
        
        # Reader development related
        ("reader", "community", "building"): ['ebook_audience_development'],
        ("subscriber", "relationship", "management"): ['ebook_audience_development'],
        ("fandom", "development", "strategy"): ['ebook_audience_development'],
        ("reader", "development"): ['ebook_audience_development'],
        
        # Brand and integration
        ("brand", "identity", "logo"): ['brand_identity_design', 'visual_design_fundamentals'],
        ("color", "system", "guidelines"): ['brand_identity_design'],
        ("motion", "animation", "movement"): ['motion_graphics', 'visual_design_fundamentals'],
        ("interactive", "effects", "dynamic"): ['motion_graphics'],
        ("campaign", "strategy", "contents"): ['visual_contents_strategy'],
        ("design", "system", "components"): ['visual_contents_strategy'],
        ("visual", "strategy", "planning"): ['visual_contents_strategy'],
        
        # contents integration
        ("integration", "contents", "creation"): ['contents_integration'],
        ("cross", "media", "assets"): ['contents_integration'],
        ("multi", "platform", "contents"): ['contents_integration'],
        ("contents", "optimization", "integration"): ['contents_optimization']
    }
    
    matched_skills = []
    for keywords, skills in skill_mapping.items():
        if any(keyword in task_description for keyword in keywords):
            matched_skills.extend(skills)
    
    return list(set(matched_skills))  # Remove duplicates
```

### HR-contents Creator Communication Protocol
```yaml
# HR → contents Creator task delivery format
hr_task:
  type: "role_evaluation"
  description: "Integrated contents creation skill analysis for contents Creator Role evaluation"
  priority: "high"
  deadline: "2026-01-17"
  
# contents Creator → HR result return format  
contents_creator_result:
  agent: "contents-creator"
  task_type: "role_evaluation"
  skills_used: ["ebook_monetization", "ebook_platform_strategy", "ebook_writing", "contents_writing_fundamentals"]
  results:
    - skill: "ebook_monetization"
      block: "INPUT_OUTPUT"
      contents: "Ebook revenue model analysis completed"
    - skill: "ebook_monetization" 
      block: "EXECUTION_LOGIC"
      contents: "Revenue model execution plan established"
    - skill: "ebook_platform_strategy"
      block: "INPUT_OUTPUT"
      contents: "Platform distribution strategy analysis completed"
    - skill: "ebook_writing"
      block: "INPUT_OUTPUT"
      contents: "Integrated contents creation requirements analysis completed"
  status: "completed"
```
