import { ReactNode } from "react";

import { FieldId } from "./chat";

function Icon({ children }: { children: ReactNode }) {
  return (
    <svg
      className="icon"
      viewBox="0 0 24 24"
      width="1em"
      height="1em"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export const SendIcon = () => (
  <Icon>
    <path d="M12 19V5" />
    <path d="M6 11l6-6 6 6" />
  </Icon>
);

export const StopIcon = () => (
  <svg className="icon" viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true">
    <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" />
  </svg>
);

export const PlusIcon = () => (
  <Icon>
    <path d="M12 5v14" />
    <path d="M5 12h14" />
  </Icon>
);

export const MenuIcon = () => (
  <Icon>
    <path d="M4 7h16" />
    <path d="M4 12h16" />
    <path d="M4 17h16" />
  </Icon>
);

export const CloseIcon = () => (
  <Icon>
    <path d="M6 6l12 12" />
    <path d="M18 6L6 18" />
  </Icon>
);

export const CopyIcon = () => (
  <Icon>
    <rect x="9" y="9" width="11" height="11" rx="2" />
    <path d="M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1" />
  </Icon>
);

export const CheckIcon = () => (
  <Icon>
    <path d="M5 12.5l4.5 4.5L19 7.5" />
  </Icon>
);

export const AlertIcon = () => (
  <Icon>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7.5v5.5" />
    <path d="M12 16.5v.01" />
  </Icon>
);

export const ChatIcon = () => (
  <Icon>
    <path d="M20 12a8 8 0 0 1-11.6 7.1L4 20l.9-4.4A8 8 0 1 1 20 12z" />
  </Icon>
);

const TaxIcon = () => (
  <Icon>
    <path d="M6 3h12v18l-3-2-3 2-3-2-3 2z" />
    <path d="M9.5 8h5" />
    <path d="M9.5 12h5" />
  </Icon>
);

const HealthIcon = () => (
  <Icon>
    <path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.4 4.3 4.3 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z" />
    <path d="M12 10v5" />
    <path d="M9.5 12.5h5" />
  </Icon>
);

const LoanIcon = () => (
  <Icon>
    <path d="M2.5 9.5L12 5l9.5 4.5L12 14z" />
    <path d="M6.5 11.5V16c0 1.2 2.5 2.5 5.5 2.5s5.5-1.3 5.5-2.5v-4.5" />
    <path d="M21.5 9.5V15" />
  </Icon>
);

export function FieldIcon({ field }: { field: FieldId }) {
  if (field === "tax") return <TaxIcon />;
  if (field === "sha") return <HealthIcon />;
  return <LoanIcon />;
}

/** An original shield mark in the colours of the Kenyan flag. */
export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg viewBox="0 0 32 32" width={size} height={size} aria-hidden="true" className="logo">
      <path d="M16 2c5 2.2 8 3 12 3 0 12-3 20-12 25C7 25 4 17 4 5c4 0 7-.8 12-3z" fill="#006600" />
      <path d="M16 2c5 2.2 8 3 12 3 0 3.300-.200 6.300-.700 9H4.700C4.200 11.300 4 8.300 4 5c4 0 7-.8 12-3z" fill="#000000" />
      <path d="M4.700 12.800h22.600c-.200 1.500-.500 3-.900 4.400H5.600c-.400-1.400-.700-2.900-.900-4.400z" fill="#ffffff" />
      <path d="M5 13.800h22c-.200 .9-.300 1.700-.600 2.400H5.600c-.300-.700-.400-1.500-.600-2.400z" fill="#bb0000" />
    </svg>
  );
}
