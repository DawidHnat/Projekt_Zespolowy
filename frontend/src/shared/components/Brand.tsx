const brandMark = `${import.meta.env.BASE_URL}brand/fleet-flow-mark.svg`;

export function Brand() {
  return (
    <a className="brand" href="#dashboard" aria-label="Fleet-Flow — dashboard">
      <img
        className="brand-mark"
        src={brandMark}
        width="46"
        height="32"
        alt=""
        aria-hidden="true"
      />
      <span className="brand-wordmark">
        Fleet <span className="brand-flow">Flow</span>
      </span>
    </a>
  );
}
