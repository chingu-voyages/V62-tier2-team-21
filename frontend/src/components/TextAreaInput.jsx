import "./Input.css";

export default function TextAreaInput({
  id,
  title,
  description,
  maxWords,
  wordCount,
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
        className={`input-control ${wordCount > maxWords ? "word-count-alert" : ""}`}
        id={id}
        name={id}
        {...props}
      />
      <div className="word-alert-container">
        <p className="error-message">{inputError[id]}</p>
        {maxWords && (
          <p
            className={`word-count ${wordCount > maxWords ? "word-count-alert" : ""}`}
          >
            {" "}
            {wordCount} / {maxWords} words max
          </p>
        )}
      </div>
    </div>
  );
}
