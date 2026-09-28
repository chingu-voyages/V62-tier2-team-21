import InputContainer from "../components/InputContainer";
import "./FormPage.css";
import Footer from "../components/layout/Footer";
import LoadingModal from "../components/LoadingModal";
import { useState } from "react";

export default function FormPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  return (
    <>
      {isSubmitting && <LoadingModal />}
      <div className="form-page" inert={isSubmitting}>
        <InputContainer
          isSubmitting={isSubmitting}
          setIsSubmitting={setIsSubmitting}
        />
        <Footer />
      </div>
    </>
  );
}
