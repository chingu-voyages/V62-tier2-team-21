import { useState, useEffect } from "react";
import "./LoadingModal.css";
import ErrorContent from "./ErrorContent";
import LoadingContent from "./LoadingContent";
import { TIMEOUT_SECONDS } from "../../constants/formConstant";

export default function LoadingModal({ generationError, handleCloseModal }) {
  const [percentage, setPercentage] = useState(0);

  useEffect(() => {
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  useEffect(() => {
    if (percentage > 100) return;

    const timer = setInterval(() => {
      setPercentage((prev) => (prev < 100 ? prev + 1 : 100));
    }, TIMEOUT_SECONDS * 10);

    return () => clearInterval(timer);
  }, [percentage]);

  return (
    <div className="back-drop">
      <div
        className={`center-container ${generationError ? "error-container" : ""}`}
      >
        {generationError ? (
          <ErrorContent
            handleCloseModal={handleCloseModal}
            generationError={generationError}
          />
        ) : (
          <LoadingContent percentage={percentage} />
        )}
      </div>
    </div>
  );
}
