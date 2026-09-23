import {
  CAREERGOAL_CHARACTERS_MAX,
  PASTEXPERIENCE_CHARACTERS_MAX,
} from "../constants/formConstant";

export function validateInput(
  careerGoal,
  pastExperience,
  careerGoalCharacterCount,
  pastExperienceCharacterCount,
) {
  const errors = {
    careerGoal: "",
    pastExperience: "",
  };

  if (careerGoalCharacterCount > CAREERGOAL_CHARACTERS_MAX) {
    errors.careerGoal = `Please keep your response within ${CAREERGOAL_CHARACTERS_MAX} characters.`;
  }

  if (careerGoal.trim() === "") {
    errors.careerGoal = "Please enter your career goal.";
  }

  if (pastExperienceCharacterCount > PASTEXPERIENCE_CHARACTERS_MAX) {
    errors.pastExperience = `Please keep your response within ${PASTEXPERIENCE_CHARACTERS_MAX} characters.`;
  }

  if (pastExperience.trim() === "") {
    errors.pastExperience = "Please enter your past experience.";
  }

  return errors;
}
