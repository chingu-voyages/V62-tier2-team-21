import { useState } from "react";
import TextAreaInput from "./TextAreaInput";
import SelectInput from "./SelectInput";
import NumberInput from "./NumberInput";
import "./InputContainer.css";
import { validateInput } from "../util/validation";
import {
  CAREERGOAL_CHARACTERS_MAX,
  PASTEXPERIENCE_CHARACTERS_MAX,
} from "../constants/formConstant";

export default function InputContainer() {
  const [inputData, setInputData] = useState({
    careerGoal: "",
    pastExperience: "",
  });

  const [inputError, setInputError] = useState({
    careerGoal: "",
    pastExperience: "",
  });

  const [submitError, setSubmitError] = useState(null);

  const [isSubmitting, setIsSubmitting] = useState(false);

  const API_URL =
    import.meta.env.VITE_API_URL || "http://localhost:8000";

  //TODO: send to backend
  async function sendData(enteredData) {
    try {
      setIsSubmitting(true);
      setSubmitError(null);
      const response = await fetch(`${API_URL}/user-input`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(enteredData),
      });

      if (!response.ok) {
        throw new Error("Failed to submit data");
      }
      return true;
    } catch (err) {
      setSubmitError(err.message);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();

    const target = e.target;

    const careerGoal = target.careerGoal.value;
    const currentSkillLevel = target.currentSkillLevel.value;
    const workingIndustry = target.workingIndustry.value;
    const pastExperience = target.pastExperience.value;
    const availableTime = +target.availableTime.value;

    const errors = validateInput(
      careerGoal,
      pastExperience,
      careerGoalCharacterCount,
      pastExperienceCharacterCount,
    );

    if (errors.careerGoal !== "" || errors.pastExperience !== "") {
      setInputError(errors);
      return;
    }

    setInputError({
      careerGoal: "",
      pastExperience: "",
    });

    console.log(
      careerGoal,
      currentSkillLevel,
      workingIndustry,
      pastExperience,
      availableTime,
    );

    const enteredData = {
      career_goal: careerGoal,
      current_skill_level: currentSkillLevel,
      working_industry: workingIndustry,
      past_experience: pastExperience,
      available_time: availableTime,
    };

    const success = await sendData(enteredData);

    //TODO: navigate to a separate page if data submission succeeds
    if (success) {
      return;
    }
  }

  function handleCount(e, id) {
    const inputValue = e.target.value;

    setInputData((prevState) => {
      return {
        ...prevState,
        [id]: inputValue,
      };
    });
  }

  const careerGoalCharacterCount = inputData.careerGoal.length;
  const pastExperienceCharacterCount = inputData.pastExperience.length;

  return (
    <form onSubmit={handleSubmit} className="input-container">
      <h2 className="input-container-title">Career & Skill Assessment Form</h2>
      <TextAreaInput
        id="careerGoal"
        title="1. Career Goal"
        description={
          <>
            Describe the professional role, position, or industry you aim to
            achieve in the future.
          </>
        }
        placeholder="e.g., To become a Lead Product Manager..."
        maxCharacters={CAREERGOAL_CHARACTERS_MAX}
        maxLength={CAREERGOAL_CHARACTERS_MAX}
        required
        onChange={(e) => handleCount(e, "careerGoal")}
        characterCount={careerGoalCharacterCount}
        inputError={inputError}
      />

      <SelectInput
        id="currentSkillLevel"
        title="2. Current Skill Level"
        description="Select current level which you currently level"
        required
        defaultValue=""
      >
        <option value="" disabled>
          -- Select your current level --
        </option>
        <option value="beginner">Beginner</option>
        <option value="intermediate">Intermediate</option>
        <option value="advanced">Advanced</option>
      </SelectInput>

      <SelectInput
        id="workingIndustry"
        title="3. Working Industry"
        description={
          <>
            Select the primary industry in which you currently work or have the
            most experience.
          </>
        }
        required
        defaultValue=""
      >
        <option value="" disabled>
          -- Select the industry --
        </option>
        <option value="frontend-development">Frontend Development</option>
        <option value="backend-development">Backend Development</option>
        <option value="data-science-ml">Data Science/ML</option>
        <option value="cybersecurity">Cybersecurity</option>
        <option value="product-management">Product Management</option>
      </SelectInput>

      <TextAreaInput
        id="pastExperience"
        title="4. Past Experience"
        description={
          <>
            Provide a brief summary of your past education, work experience, or
            relevant competencies.
          </>
        }
        placeholder="e.g., Bachelor's in Computer Science..."
        maxCharacters={PASTEXPERIENCE_CHARACTERS_MAX}
        maxLength={PASTEXPERIENCE_CHARACTERS_MAX}
        onChange={(e) => handleCount(e, "pastExperience")}
        characterCount={pastExperienceCharacterCount}
        inputError={inputError}
        required
      />

      <NumberInput
        id="availableTime"
        title="5. Available Time / Time Commitment"
        description={
          <>
            Indicate the average number of hours per week you can dedicate to
            this program.
          </>
        }
        required
        min="1"
        max="168"
      />

      {submitError && <p>{submitError}</p>}
      <button
        type="submit"
        className="input-submit-button"
        disabled={isSubmitting}
      >
        Submit Information
      </button>
    </form>
  );
}
