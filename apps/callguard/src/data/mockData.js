/**
 * CallGuard Seeded Demo Data
 * 
 * Strict requirement: ALL records are synthetic demo data.
 * No real customer information or live phone numbers are stored.
 */

export const demoAgents = [
  {
    id: "agt_101",
    username: "agent.sarah",
    name: "Sarah Jenkins",
    role: "Senior Security Specialist",
    queue: "High-Value Verification",
    avatar: "SJ"
  },
  {
    id: "agt_102",
    username: "agent.david",
    name: "David Chen",
    role: "Tier 2 Fraud Investigator",
    queue: "Escalated Vishing Review",
    avatar: "DC"
  }
];

export const demoCustomers = [
  {
    customerRef: "customer_001",
    displayName: "Pseudonymous Client A",
    accountTier: "Premier Corporate",
    registeredPhone: "+1-555-0192 (Simulated)",
    enrolledBiometrics: true,
    riskRating: "Low"
  },
  {
    customerRef: "customer_002",
    displayName: "Pseudonymous Client B",
    accountTier: "Retail Banking",
    registeredPhone: "+1-555-0144 (Simulated)",
    enrolledBiometrics: true,
    riskRating: "Medium"
  },
  {
    customerRef: "customer_003",
    displayName: "Pseudonymous Client C",
    accountTier: "Private Wealth",
    registeredPhone: "+1-555-0188 (Simulated)",
    enrolledBiometrics: false,
    riskRating: "High"
  }
];

export const demoCalls = [
  {
    id: "CALL-2026-1001",
    customerRef: "customer_001",
    channel: "Inbound IVR Transfer",
    status: "IN_PROGRESS",
    duration: 142, // seconds
    scenarioName: "Scenario 1: Routine Transfer Verification",
    scenarioDescription: "Normal customer requesting wire status. Routine challenge phrase authentication.",
    demo: true,
    riskLevel: "LOW",
    reasonPublic: "ROUTINE_TRANSACTION",
    recommendedAction: "VERIFY_VOICE",
    verificationStatus: "PENDING_CHALLENGE",
    transcript: [
      { id: "seg_1", speaker: "agent", text: "Thank you for calling Secure Trust. My name is Sarah. How can I help you today?", timestamp: "00:05" },
      { id: "seg_2", speaker: "caller", text: "Hi Sarah, I would like to check on the status of my pending international wire transfer.", timestamp: "00:14" },
      { id: "seg_3", speaker: "agent", text: "I can certainly look into that wire for you. For high-value release, I will need to initiate a voice security challenge.", timestamp: "00:26" },
      { id: "seg_4", speaker: "caller", text: "Understood, please go ahead with the prompt.", timestamp: "00:32" }
    ]
  },
  {
    id: "CALL-2026-1002",
    customerRef: "customer_002",
    channel: "Direct Priority Queue",
    status: "IN_PROGRESS",
    duration: 89,
    scenarioName: "Scenario 2: Suspected Urgent Credential Solicit (Vishing)",
    scenarioDescription: "Caller claims urgent IT security lock, pressures agent, solicit password/OTP.",
    demo: true,
    riskLevel: "HIGH",
    reasonPublic: "URGENT_CREDENTIAL_SOLICITATION",
    recommendedAction: "ESCALATE_HUMAN_REVIEW",
    verificationStatus: "FAILED_CHALLENGE",
    transcript: [
      { id: "seg_10", speaker: "caller", text: "Listen to me, I am the director of corporate finance and my executive portal is locked right now!", timestamp: "00:04" },
      { id: "seg_11", speaker: "agent", text: "Sir, I understand your urgency, but I need to follow standard identity verification.", timestamp: "00:12" },
      { id: "seg_12", speaker: "caller", text: "No time for procedures! Bypass the OTP immediately and read back the authorization code or I will have your supervisor terminate you!", timestamp: "00:21" },
      { id: "seg_13", speaker: "agent", text: "I cannot bypass secondary authentication or reveal one-time codes.", timestamp: "00:30" }
    ]
  },
  {
    id: "CALL-2026-1003",
    customerRef: "customer_003",
    channel: "Fraud Advisory Callback",
    status: "WAITING",
    duration: 35,
    scenarioName: "Scenario 3: Genuine Security Advisory (Hard Negative)",
    scenarioDescription: "Agent reminds client: 'Never share your OTP with anyone.' Verifies AAA-VR does not false positive.",
    demo: true,
    riskLevel: "LOW",
    reasonPublic: "SECURITY_AWARENESS_WARNING",
    recommendedAction: "NONE",
    verificationStatus: "NOT_INITIATED",
    transcript: [
      { id: "seg_20", speaker: "agent", text: "As a security precaution from our Fraud Prevention Unit, remember we will never ask you to share your OTP or password.", timestamp: "00:08" },
      { id: "seg_21", speaker: "caller", text: "Thank you for the reminder. I received an odd text earlier asking for my code, which made me call you.", timestamp: "00:18" },
      { id: "seg_22", speaker: "agent", text: "You did the right thing. Let us verify your account safely.", timestamp: "00:27" }
    ]
  }
];

export const demoAuditLogs = [
  {
    id: "AUD-9901",
    timestamp: "2026-11-11T16:20:11Z",
    requestId: "req_9f3b2a81-c001",
    customerRef: "customer_001",
    tenantId: "callcentre_demo",
    decision: "APPROVE",
    riskLevel: "LOW",
    reasonPublic: "REQUIRED_CHECKS_PASSED",
    actionTaken: "Wire released upon challenge confirmation"
  },
  {
    id: "AUD-9902",
    timestamp: "2026-11-11T16:45:33Z",
    requestId: "req_4c1e87d0-c002",
    customerRef: "customer_002",
    tenantId: "callcentre_demo",
    decision: "DENY",
    riskLevel: "HIGH",
    reasonPublic: "CHALLENGE_MISMATCH",
    actionTaken: "Escalated to Fraud Supervisor Tier 2"
  }
];
