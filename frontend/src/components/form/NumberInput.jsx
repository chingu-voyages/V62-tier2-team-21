import "./Input.css";

export default function NumberInput({
  id,
  title,
  description,
  children,
  ...props
}) {
  return (
    <div className="input-item">
      <label htmlFor={id} className="input-title">
        {title}
      </label>
      <p className="input-description">{description}</p>
      <input
        className="input-control"
        id={id}
        name={id}
        {...props}
        type="number"
      />
      {children}
    </div>
  );
}
