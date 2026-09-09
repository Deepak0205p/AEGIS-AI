# Air-Gap Network Isolation & Sovereign Cryptographic Verification Specification
**Document Reference:** `SOP-DEF-AIRGAP-SEC-004` | **Domain:** `DEFENCE`  
**Regulatory Clause:** MoD Cyber Security Manual Sec 8.4 | **Page / Section:** Page 22-26  
**Equipment Tags:** SEC-NODE-01, GPU-SRV-AIRGAP  
**Keywords:** air gap, sovereign, cybersecurity, zero egress, network isolation, tempest, cryptographic, sha256

---

## Technical & Regulatory Policy Content

Sovereign Air-Gap Network Security & Isolation Criteria for Defence R&D Units: 1. Physical & Logical Air-Gap: Host servers executing sensitive knowledge work must have zero WAN physical uplinks, disabled 802.11 Wi-Fi, Bluetooth, and cellular modems at BIOS/kernel level. 2. Real-time Outbound Socket Guard: Runtime network monitors must enforce 0 bytes egress to external IP addresses. Any non-loopback outbound SYN packet triggers immediate alert and connection termination. 3. Data Deliverables: All generated reports (DOCX, PPTX, XLSX) must be cryptographically hashed using SHA-256 for local audit provenance and non-repudiation. 4. On-Premise GPU Inference: LLM models must run entirely inside workstation VRAM/RAM via local Ollama socket without telemetry or external API calls.

---

*Verified On-Premises Master Technical Specification — Grounded for Sovereign RAG Indexing.*
