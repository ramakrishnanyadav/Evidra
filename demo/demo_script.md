# Evidra Demo Script

**Preparation:**
- Ensure Backend Server (`uvicorn main:app --port 8001`) is running.
- Ensure Frontend Server is serving `index.html`.
- Login to the UI.

## Scene 1: Setting the Stage
- Toggle **Blind Review ON**.
- Explain: *"Traditional screening focuses on names and pedigrees. We focus on evidence."*

## Scene 2: Candidate Upload
- Click **Upload Resume**.
- Select `arjun_resume.pdf`.
- Explain: *"We're uploading a typical resume. The candidate claims to be a standard backend developer."*

## Scene 3: The Timeline
- Watch the **Timeline Animate**.
- Call out the phases: *"Resume Uploaded → Data Extracted → Embedding Generated → GitHub Synced"*
- **Expected Wow Moment:** The timeline hits **Hidden Strength Found** and glows gold.

## Scene 4: The Graph
- Open the **Competency Graph** (if applicable).
- Point to the new gold node.
- Explain: *"Our system discovered a capability the candidate didn't even mention on their resume."*

## Scene 5: Explainability Breakdown
- Open the **Explainability Panel** (Why ranked #1?).
- Highlight the tags:
  - **VERIFIED SKILLS:** HIGH IMPACT
  - **HIDDEN STRENGTH:** CRITICAL IMPACT
- Explain: *"This isn't a black box. Evidra tells you exactly why this candidate is a high-value target."*

## Scene 6: The Arjun Moment (Search)
- Go to the **Command Bar**.
- Enter query: *"Find candidates stronger than their resume suggests"*
- Press **Enter**.
- **Expected:** Arjun surfaces as the #1 candidate.

## Scene 7: The Evidence
- Open the candidate details.
- Show the GitHub evidence side-by-side with the resume.
- Explain: *"The resume says 'Backend Developer'. The evidence proves 'Distributed Systems Engineer'. Evidra finds the talent your competitors miss."*
