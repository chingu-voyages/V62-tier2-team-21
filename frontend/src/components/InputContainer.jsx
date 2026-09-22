import { useState } from "react";
import TextAreaInput from "./TextAreaInput";
import SelectInput from "./SelectInput";
import NumberInput from "./NumberInput";
import "./InputContainer.css";
import { validateInput } from "../util/validation";
import {
  CAREERGOAL_WORD_MAX,
  PASTEXPERIENCE_WORD_MAX,
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

  //TODO: send to backend
  async function sendData(enteredData) {
    try {
      setIsSubmitting(true);
      setSubmitError(null);
      const response = await fetch("http://localhost:8000/user-input", {
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
    const availableTime = target.availableTime.value;

    const errors = validateInput(
      careerGoal,
      pastExperience,
      careerGoalWordCount,
      pastExperienceWordCount,
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
      available_time: +availableTime,
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

  const careerGoalWordCount =
    inputData.careerGoal.trim() === ""
      ? 0
      : inputData.careerGoal.trim().split(/\s+/).length;

  const pastExperienceWordCount =
    inputData.pastExperience.trim() === ""
      ? 0
      : inputData.pastExperience.trim().split(/\s+/).length;

  return (
    <form onSubmit={handleSubmit} className="input-container">
      <h2 className="input-container-title">Career & Skill Assessment Form</h2>
      <TextAreaInput
        id="careerGoal"
        title="1. Career Goal"
        description={
          <>
            Describe the professional role, position, or industry
            <br />
            you aim to achieve in the future.
          </>
        }
        placeholder="e.g., To become a Lead Product Manager..."
        maxWords={CAREERGOAL_WORD_MAX}
        required
        onChange={(e) => handleCount(e, "careerGoal")}
        wordCount={careerGoalWordCount}
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
            Select the primary industry in which you currently <br /> work or
            have the most experience.
          </>
        }
        required
        defaultValue=""
      >
        <option value="" disabled>
          -- Select the industry --
        </option>
        <option value="1">industry test1</option>
        <option value="2">industry test2</option>
        <option value="3">industry test3</option>
      </SelectInput>

      <TextAreaInput
        id="pastExperience"
        title="4. Past Experience"
        description={
          <>
            Provide a brief summary of your past <br />
            education, work experience, <br /> or relevant competencies.
          </>
        }
        placeholder="e.g., Bachelor's in Computer Science..."
        maxWords={PASTEXPERIENCE_WORD_MAX}
        onChange={(e) => handleCount(e, "pastExperience")}
        wordCount={pastExperienceWordCount}
        inputError={inputError}
        required
      />

      <NumberInput
        id="availableTime"
        title="5. Available Time / Time Commitment"
        description={
          <>
            Indicate the average number of hours per week you <br /> can
            dedicate to this program.
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
