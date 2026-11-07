import { FieldId } from "./chat";

export interface FieldInfo {
  id: FieldId;
  name: string;
  agency: string;
  summary: string;
  placeholder: string;
  examples: string[];
}

export const FIELDS: FieldInfo[] = [
  {
    id: "tax",
    name: "Tax",
    agency: "KRA",
    summary: "PAYE, VAT, rental income, turnover tax and compliance certificates",
    placeholder: "Ask about PAYE, VAT or rental income",
    examples: [
      "What is the VAT rate?",
      "When must employers remit PAYE?",
      "How much tax do landlords pay on rent?",
      "Which businesses pay turnover tax?",
    ],
  },
  {
    id: "sha",
    name: "Health cover",
    agency: "SHA",
    summary: "Registering with the Social Health Authority, means testing and health funds",
    placeholder: "Ask about SHA registration or cover",
    examples: [
      "How do I register for SHA?",
      "Can I register by phone?",
      "What is means testing?",
      "How many health funds are there?",
    ],
  },
  {
    id: "helb",
    name: "Student loans",
    agency: "HELB",
    summary: "Applying for loans, repayment, statements and compliance certificates",
    placeholder: "Ask about your HELB loan",
    examples: [
      "When do I start repaying my HELB loan?",
      "How do I get a HELB compliance certificate?",
      "How do I download my loan statement?",
      "Who confirms that my loan is fully repaid?",
    ],
  },
];

export function fieldById(id: FieldId): FieldInfo {
  return FIELDS.find((field) => field.id === id)!;
}
