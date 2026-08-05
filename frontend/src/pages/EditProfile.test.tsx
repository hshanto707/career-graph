import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/hooks/useAuth";
import { AUTH_STORAGE_KEY } from "@/lib/apiClient";
import EditProfile from "@/pages/EditProfile";
import { profileApi, type ProfileOut } from "@/lib/api/profile";

vi.mock("@/lib/api/profile", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/profile")>("@/lib/api/profile");
  return {
    ...actual,
    profileApi: {
      ...actual.profileApi,
      get: vi.fn(),
      update: vi.fn(),
      addOrUpdateSkill: vi.fn(),
    },
  };
});

const mockedGet = vi.mocked(profileApi.get);
const mockedUpdate = vi.mocked(profileApi.update);
const mockedAddSkill = vi.mocked(profileApi.addOrUpdateSkill);

const BASE_PROFILE: ProfileOut = {
  id: "p1",
  user_id: "u1",
  major: "Computer Science",
  graduation_year: 2026,
  skills: [{ name: "Python", proficiency: 8, years: 3 }],
  target_roles: ["Data Analyst"],
  experience: [],
  updated_at: "2026-01-01T00:00:00Z",
};

function renderEditProfile() {
  window.localStorage.setItem(
    AUTH_STORAGE_KEY,
    JSON.stringify({ token: "tok-1", user: { id: "u1", email: "alex@school.edu", name: "Alex Chen" } })
  );
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={["/profile/edit"]}>
          <Routes>
            <Route path="/profile/edit" element={<EditProfile />} />
            <Route path="/profile" element={<div>Profile Page</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe("EditProfile page", () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockedGet.mockReset();
    mockedUpdate.mockReset();
    mockedAddSkill.mockReset();
    mockedGet.mockResolvedValue(BASE_PROFILE);
  });

  it("pre-fills the form with current profile data", async () => {
    renderEditProfile();

    await waitFor(() => expect(screen.getByDisplayValue("Computer Science")).toBeInTheDocument());
    expect(screen.getByDisplayValue("2026")).toBeInTheDocument();
    expect(screen.getByText(/Python/)).toBeInTheDocument();
    expect(screen.getByText("Data Analyst")).toBeInTheDocument();
  });

  it("adds a skill via the skills endpoint and shows it without a full reload, rejecting duplicates", async () => {
    const updatedProfile = {
      ...BASE_PROFILE,
      skills: [...BASE_PROFILE.skills, { name: "React", proficiency: 4, years: 1 }],
    };
    mockedAddSkill.mockResolvedValue(updatedProfile);

    renderEditProfile();
    await waitFor(() => expect(screen.getByDisplayValue("Computer Science")).toBeInTheDocument());

    // Duplicate is rejected without calling the API.
    fireEvent.change(screen.getByLabelText(/skill name/i), { target: { value: "Python" } });
    fireEvent.click(screen.getByRole("button", { name: /add skill/i }));
    await waitFor(() => expect(screen.getByText(/already in your skill list/i)).toBeInTheDocument());
    expect(mockedAddSkill).not.toHaveBeenCalled();

    // A genuinely new skill calls the endpoint and appears in the list.
    fireEvent.change(screen.getByLabelText(/skill name/i), { target: { value: "React" } });
    fireEvent.click(screen.getByRole("button", { name: /add skill/i }));

    await waitFor(() => expect(mockedAddSkill).toHaveBeenCalledWith({
      name: "React",
      proficiency: 5,
      years: 0,
    }));
    await waitFor(() => expect(screen.getByText(/React/)).toBeInTheDocument());
  });

  it("removes a skill via profile update and reflects the change in the list", async () => {
    const updatedProfile = { ...BASE_PROFILE, skills: [] };
    mockedUpdate.mockResolvedValue(updatedProfile);

    renderEditProfile();
    await waitFor(() => expect(screen.getByDisplayValue("Computer Science")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /remove python/i }));

    await waitFor(() => expect(mockedUpdate).toHaveBeenCalledWith({ skills: [] }));
    await waitFor(() => expect(screen.getByText(/no skills added yet/i)).toBeInTheDocument());
  });

  it("shows 'Graduation Year' once a past year is selected, and 'Expected Graduation Year' for the current/future default", async () => {
    renderEditProfile();
    await waitFor(() => expect(screen.getByDisplayValue("Computer Science")).toBeInTheDocument());

    expect(screen.getByText(/expected graduation year/i)).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText(/expected graduation year/i));
    fireEvent.click(await screen.findByRole("option", { name: "2020" }));

    expect(screen.getByText(/^graduation year$/i)).toBeInTheDocument();
    expect(screen.queryByText(/expected graduation year/i)).not.toBeInTheDocument();
  });

  it("saves valid changes via PUT /profile and navigates back to the view", async () => {
    mockedUpdate.mockResolvedValue({ ...BASE_PROFILE, major: "Data Science" });

    renderEditProfile();
    await waitFor(() => expect(screen.getByDisplayValue("Computer Science")).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(/^major$/i), { target: { value: "Data Science" } });
    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => expect(mockedUpdate).toHaveBeenCalled());
    const payload = mockedUpdate.mock.calls[0][0];
    expect(payload.major).toBe("Data Science");
    expect(payload.graduation_year).toBe(2026);
    expect(payload.target_roles).toEqual(["Data Analyst"]);

    await waitFor(() => expect(screen.getByText("Profile Page")).toBeInTheDocument());
  });

  it("allows saving with zero skills and zero target roles", async () => {
    mockedGet.mockResolvedValue({ ...BASE_PROFILE, skills: [], target_roles: [] });
    mockedUpdate.mockResolvedValue({ ...BASE_PROFILE, skills: [], target_roles: [] });

    renderEditProfile();
    await waitFor(() => expect(screen.getByDisplayValue("Computer Science")).toBeInTheDocument());
    expect(screen.getByText(/no skills added yet/i)).toBeInTheDocument();
    expect(screen.getByText(/no target roles set yet/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => expect(mockedUpdate).toHaveBeenCalled());
    expect(mockedUpdate.mock.calls[0][0].skills).toEqual([]);
    expect(mockedUpdate.mock.calls[0][0].target_roles).toEqual([]);
  });

  it("adds an experience entry with structured start/end dates and saves it", async () => {
    mockedUpdate.mockResolvedValue(BASE_PROFILE);

    renderEditProfile();
    await waitFor(() => expect(screen.getByDisplayValue("Computer Science")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /add experience/i }));

    fireEvent.change(screen.getByLabelText(/experience 1 title/i), { target: { value: "Intern" } });
    fireEvent.change(screen.getByLabelText(/experience 1 company/i), { target: { value: "Acme" } });

    fireEvent.click(screen.getByLabelText(/experience 1 start month/i));
    fireEvent.click(await screen.findByRole("option", { name: "June" }));
    fireEvent.click(screen.getByLabelText(/experience 1 start year/i));
    fireEvent.click(await screen.findByRole("option", { name: "2024" }));

    fireEvent.click(screen.getByLabelText(/experience 1 end month/i));
    fireEvent.click(await screen.findByRole("option", { name: "August" }));
    fireEvent.click(screen.getByLabelText(/experience 1 end year/i));
    fireEvent.click(await screen.findByRole("option", { name: "2024" }));

    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => expect(mockedUpdate).toHaveBeenCalled());
    expect(mockedUpdate.mock.calls[0][0].experience).toEqual([
      {
        title: "Intern",
        company: "Acme",
        start_month: 6,
        start_year: 2024,
        end_month: 8,
        end_year: 2024,
        is_current: false,
        description: "",
      },
    ]);
  });

  it("checking 'I currently work here' hides and clears the end date", async () => {
    mockedUpdate.mockResolvedValue(BASE_PROFILE);

    renderEditProfile();
    await waitFor(() => expect(screen.getByDisplayValue("Computer Science")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /add experience/i }));
    fireEvent.change(screen.getByLabelText(/experience 1 title/i), { target: { value: "Intern" } });
    fireEvent.change(screen.getByLabelText(/experience 1 company/i), { target: { value: "Acme" } });

    expect(screen.getByLabelText(/experience 1 end month/i)).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText(/currently work here/i));
    expect(screen.queryByLabelText(/experience 1 end month/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => expect(mockedUpdate).toHaveBeenCalled());
    expect(mockedUpdate.mock.calls[0][0].experience[0]).toMatchObject({
      is_current: true,
      end_month: null,
      end_year: null,
    });
  });

  it("blocks save when an experience entry is missing an end date and isn't marked current", async () => {
    renderEditProfile();
    await waitFor(() => expect(screen.getByDisplayValue("Computer Science")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /add experience/i }));
    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => expect(mockedUpdate).not.toHaveBeenCalled());
    expect(screen.queryByText("Profile Page")).not.toBeInTheDocument();
  });
});
