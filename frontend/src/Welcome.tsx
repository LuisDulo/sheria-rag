import { FieldId } from "./chat";
import { FIELDS, fieldById } from "./fields";
import { FieldIcon, Logo } from "./Icons";

export function FieldPicker({ onPick }: { onPick: (field: FieldId) => void }) {
  return (
    <section className="welcome">
      <Logo size={52} />
      <h1>Habari! What do you need help with?</h1>
      <p>Choose a topic to start.</p>
      <div className="field-cards">
        {FIELDS.map((field) => (
          <button
            key={field.id}
            type="button"
            className={`field-card field-card-${field.id}`}
            onClick={() => onPick(field.id)}
          >
            <span className="field-card-icon">
              <FieldIcon field={field.id} />
            </span>
            <span className="field-card-name">
              {field.name} <small>{field.agency}</small>
            </span>
            <span className="field-card-summary">{field.summary}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

interface FieldStartProps {
  field: FieldId;
  onAsk: (question: string) => void;
}

export function FieldStart({ field, onAsk }: FieldStartProps) {
  const info = fieldById(field);
  return (
    <section className="welcome">
      <span className={`field-badge field-card-${field}`}>
        <FieldIcon field={field} />
      </span>
      <h1>Ask about {info.name.toLowerCase()}</h1>
      <div className="suggestions">
        {info.examples.map((example) => (
          <button key={example} type="button" onClick={() => onAsk(example)}>
            {example}
          </button>
        ))}
      </div>
    </section>
  );
}
