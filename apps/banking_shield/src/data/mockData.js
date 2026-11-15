/**
 * Banking Shield Mock Data
 *
 * Demo accounts and transactions for the Banking Shield demo.
 * No real money movement per HOST_APPS.md.
 */

export const DEMO_ACCOUNTS = [
  {
    id: "user_001",
    name: "Alice Johnson",
    email: "alice@bank.demo",
    password: "demo123",
    userRef: "u_alice_001",
    hasVoiceprint: true,
    accounts: [
      {
        id: "acc_001",
        name: "Checking Account",
        number: "1234567890",
        type: "checking",
        balance: 15420.50
      },
      {
        id: "acc_002",
        name: "Savings Account",
        number: "0987654321",
        type: "savings",
        balance: 52800.00
      }
    ]
  },
  {
    id: "user_002",
    name: "Bob Smith",
    email: "bob@bank.demo",
    password: "demo123",
    userRef: "u_bob_002",
    hasVoiceprint: false,
    accounts: [
      {
        id: "acc_003",
        name: "Checking Account",
        number: "5555666677",
        type: "checking",
        balance: 8750.25
      }
    ]
  },
  {
    id: "user_003",
    name: "Carol Davis",
    email: "carol@bank.demo",
    password: "demo123",
    userRef: "u_carol_003",
    hasVoiceprint: true,
    accounts: [
      {
        id: "acc_004",
        name: "Premium Checking",
        number: "9999888877",
        type: "checking",
        balance: 125000.00
      },
      {
        id: "acc_005",
        name: "Investment Account",
        number: "1111222233",
        type: "investment",
        balance: 450000.00
      }
    ]
  }
];

export const DEMO_BENEFICIARIES = [
  {
    id: "ben_001",
    name: "John Wilson",
    bank: "First National Bank",
    accountNumber: "****4567"
  },
  {
    id: "ben_002",
    name: "Electric Company",
    bank: "Utility Bank",
    accountNumber: "****8901"
  },
  {
    id: "ben_003",
    name: "Sarah Miller",
    bank: "Community Credit Union",
    accountNumber: "****2345"
  },
  {
    id: "ben_004",
    name: "Acme Corporation",
    bank: "Business Bank",
    accountNumber: "****6789"
  }
];

export const DEMO_TRANSACTIONS = [
  // Alice's checking account
  {
    id: "tx_001",
    accountId: "acc_001",
    date: "2026-11-14",
    description: "Payroll Deposit",
    type: "credit",
    amount: 3500.00
  },
  {
    id: "tx_002",
    accountId: "acc_001",
    date: "2026-11-13",
    description: "Electric Company",
    type: "debit",
    amount: 125.50
  },
  {
    id: "tx_003",
    accountId: "acc_001",
    date: "2026-11-12",
    description: "Grocery Store",
    type: "debit",
    amount: 87.25
  },
  {
    id: "tx_004",
    accountId: "acc_001",
    date: "2026-11-10",
    description: "Transfer to Savings",
    type: "transfer",
    amount: 500.00
  },
  // Alice's savings account
  {
    id: "tx_005",
    accountId: "acc_002",
    date: "2026-11-10",
    description: "Transfer from Checking",
    type: "credit",
    amount: 500.00
  },
  {
    id: "tx_006",
    accountId: "acc_002",
    date: "2026-11-01",
    description: "Interest Payment",
    type: "credit",
    amount: 45.20
  },
  // Bob's checking account
  {
    id: "tx_007",
    accountId: "acc_003",
    date: "2026-11-14",
    description: "Freelance Payment",
    type: "credit",
    amount: 2000.00
  },
  {
    id: "tx_008",
    accountId: "acc_003",
    date: "2026-11-11",
    description: "Rent Payment",
    type: "debit",
    amount: 1500.00
  },
  // Carol's accounts
  {
    id: "tx_009",
    accountId: "acc_004",
    date: "2026-11-14",
    description: "Wire Transfer Received",
    type: "credit",
    amount: 25000.00
  },
  {
    id: "tx_010",
    accountId: "acc_005",
    date: "2026-11-12",
    description: "Dividend Payment",
    type: "credit",
    amount: 1250.00
  }
];

/**
 * Demo scenarios as specified in HOST_APPS.md §3
 */
export const DEMO_SCENARIOS = [
  {
    id: "scenario_1",
    name: "Enrolled genuine speaker, correct phrase",
    expected: "APPROVE",
    user: "alice@bank.demo"
  },
  {
    id: "scenario_2",
    name: "Wrong phrase spoken",
    expected: "DENY",
    user: "alice@bank.demo"
  },
  {
    id: "scenario_3",
    name: "Expired challenge",
    expected: "DENY",
    user: "alice@bank.demo"
  },
  {
    id: "scenario_4",
    name: "High-risk transaction step-up",
    expected: "STEP_UP",
    user: "carol@bank.demo"
  },
  {
    id: "scenario_5",
    name: "User without voice enrollment",
    expected: "REDIRECT_TO_ENROLLMENT",
    user: "bob@bank.demo"
  }
];
