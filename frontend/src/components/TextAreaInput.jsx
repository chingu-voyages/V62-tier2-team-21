import "./Input.css";

export default function TextAreaInput({
  id,
  title,
  description,
  maxCharacters,
  characterCount,
  inputError,
  ...props
}) {
  return (
    <div className="input-item">
      <label htmlFor={id} className="input-title">
        {title}
      </label>
      <p className="input-description">{description}</p>
      <textarea
        className={`input-control ${characterCount > maxCharacters ? "word-count-alert" : ""}`}
        id={id}
        name={id}
        {...props}
      />
      <div className="word-alert-container">
        <p className="error-message">{inputError[id]}</p>
        {maxCharacters && (
          <p
            className={`word-count ${characterCount > maxCharacters ? "word-count-alert" : ""}`}
          >
            {" "}
            {characterCount} / {maxCharacters} characters max
          </p>
        )}
      </div>
    </div>
  );
}
