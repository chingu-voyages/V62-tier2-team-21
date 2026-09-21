import "./Input.css";

export default function SelectInput({
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
      <select className="input-control" id={id} name={id} {...props}>
        {children}
      </select>
    </div>
  );
}
