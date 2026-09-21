import {
  CAREERGOAL_WORD_MAX,
  PASTEXPERIENCE_WORD_MAX,
} from "../constants/formConstant";

export function validateInput(
  careerGoal,
  pastExperience,
  careerGoalWordCount,
  pastExperienceWordCount,
) {
  const errors = {
    careerGoal: "",
    pastExperience: "",
  };

  if (careerGoalWordCount > CAREERGOAL_WORD_MAX) {
    errors.careerGoal = `Please keep your response within ${CAREERGOAL_WORD_MAX} words.`;
  }

  if (careerGoal.trim() === "") {
    errors.careerGoal = "Please enter your career goal.";
  }

  if (pastExperienceWordCount > PASTEXPERIENCE_WORD_MAX) {
    errors.pastExperience = `Please keep your response within ${PASTEXPERIENCE_WORD_MAX} words.`;
  }

  if (pastExperience.trim() === "") {
    errors.pastExperience = "Please enter your past experience.";
  }

  return errors;
}
