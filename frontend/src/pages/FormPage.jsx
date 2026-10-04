import InputContainer from "../components/form/InputContainer";
import "./FormPage.css";

import LoadingModal from "../components/loading/LoadingModal";
import { useState } from "react";

export default function FormPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generationError, setGenerationError] = useState(null);

  function handleCloseModal() {
    setIsSubmitting(false);
  }
  return (
    <>
      {isSubmitting && (
        <LoadingModal
          setGenerationError={setGenerationError}
          generationError={generationError}
          handleCloseModal={handleCloseModal}
        />
      )}
      <div className="form-page" inert={isSubmitting}>
        <InputContainer
          isSubmitting={isSubmitting}
          setIsSubmitting={setIsSubmitting}
          setGenerationError={setGenerationError}
        />
      </div>
    </>
  );
}
