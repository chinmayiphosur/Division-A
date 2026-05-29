# Division A — Hackathon Submission Repository

Welcome to the Division A repository. This is where all Division A teams submit their projects. Read this entire page before you start.

---

## How submissions work

You do **not** get direct write access to this repository. Instead, every team submits using the standard fork and pull request flow:

1. You make your own copy of this repository (a fork).
2. You add your project inside your own team folder in that copy.
3. You open ONE pull request to send it back here.
4. You keep updating that same pull request until the deadline.

> [!IMPORTANT]
> **Every team has its own folder under `teams/`, for example `teams/team-01`, `teams/team-02`, and so on. You must put your work ONLY inside the folder assigned to your team. Do not add, edit, rename, or delete files in any other team's folder or anywhere else in the repository.**

---

## Before you start

You only need one thing: a free GitHub account. If you do not have one, create it at github.com (takes about a minute). You do not need to be invited or added by anyone.

---

## Step 1 — Fork this repository

1. At the top-right of this repository page, click the **Fork** button.
2. On the next screen, **UNCHECK the box that says "Copy the `main` branch only"** so that your fork copies the full repository, then click **Create fork**.
3. You now have your own copy under your own account. All your work happens in this copy.

> [!WARNING]
> **Do not skip unchecking "Copy the `main` branch only". If you leave it checked you may not get the complete repository structure.**

---

## Step 2 — Add your project to your team folder

Work inside **your fork** (the copy under your own username), not this original repository.

1. Navigate into your team folder, for example `teams/team-05`.
2. Click **Add file**, then **Upload files**.
3. Drag in your project files.

> [!WARNING]
> **Make sure your files land inside your team folder and nowhere else. Before committing, check that the path at the top of the page reads something like `your-username/division-a/teams/team-05`. If your files are not inside your team folder, your submission may not be counted.**

4. Scroll down to the **Commit changes** section.

> [!IMPORTANT]
> **At this step you will see two options. Choose "Commit directly to the `main` branch". Do NOT choose "Create a new branch for this commit and start a pull request". Committing directly to `main` means you can keep uploading files one by one without creating a new pull request every time.**

5. Click **Commit changes**.

You can repeat this step as many times as you need to add more files. Every upload goes onto the same `main` branch of your fork.

---

## Step 3 — Open ONE pull request

Do this only once, after your first upload.

1. Go back to the main page of your fork.
2. GitHub usually shows a banner near the top with a **Contribute** option, or a message that your branch is ahead. Click **Contribute**, then **Open pull request**.
3. If you do not see that banner, click the **Pull requests** tab, then **New pull request**.
4. Confirm the pull request is set to merge **into the original Division A repository, branch `main`**.
5. Give it a clear title, for example `Team 05 submission`.
6. Click **Create pull request**.

That is it. Your submission is now a pull request that the organizers can see.

---

## Updating your submission

> [!IMPORTANT]
> **Do NOT open a new pull request for every change. Keep using your ONE pull request. Just keep uploading files or committing changes to the `main` branch of your fork (Step 2). Your existing pull request updates automatically with every new commit.**

A new pull request is only ever needed if your single pull request gets closed. As long as it stays open, everything you push keeps flowing into it.

---

## Option B — Pushing from the command line (VS Code, Colab, or a terminal)

If you build your project in VS Code, Google Colab, or any local terminal, you can push with `git` instead of uploading through the website. You still fork first (Step 1 above), then use the commands below.

### One-time setup: get a Personal Access Token

> [!WARNING]
> **When git asks for a password, your normal GitHub account password will NOT work. You must use a Personal Access Token instead.**

To create one:
1. Go to github.com, then **Settings** (your profile menu) > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
2. Click **Generate new token (classic)**.
3. Give it a name, set an expiry, and tick the **`repo`** checkbox.
4. Click **Generate token** and copy the token. Save it somewhere safe; you cannot see it again.

### Pushing from VS Code or a local terminal

Replace `your-username` with your GitHub username and `team-05` with your team folder.

```bash
# 1. Clone YOUR fork (not the original repo)
git clone https://github.com/your-username/division-a.git
cd division-a

# 2. Put your project files inside your team folder only
#    e.g. teams/team-05/

# 3. Stage, commit, and push to your fork's main branch
git add teams/team-05
git commit -m "Team 05 submission"
git push origin main
```

When prompted, enter your GitHub **username**, and paste your **Personal Access Token** as the password.

For every later update, just repeat:

```bash
git add teams/team-05
git commit -m "update"
git push origin main
```

In **VS Code** specifically, you can also use the built-in "Sign in to GitHub" popup, which handles the token for you, then use the Source Control panel to commit and push instead of typing commands.

### Pushing from Google Colab

In a Colab code cell, prefix each command with `!`, and put your token directly in the clone URL:

```python
# Clone your fork using your token
!git clone https://YOUR_TOKEN@github.com/your-username/division-a.git
%cd division-a

# After adding files into teams/team-05/
!git config --global user.email "you@example.com"
!git config --global user.name "Your Name"
!git add teams/team-05
!git commit -m "Team 05 submission"
!git push origin main
```

> [!WARNING]
> **Do not share a Colab notebook that still contains your Personal Access Token in the code. Anyone who sees the token can access your account. Remove it before sharing.**

After pushing from the command line, open ONE pull request the same way as Step 3 above. Future pushes update that same pull request automatically.

---

## Pulling the latest changes from this repository

If the organizers update this repository and you want those changes in your fork:

**On the website:** open your fork's main page, click **Sync fork**, then **Update branch**.

**On the command line:**

```bash
git remote add upstream https://github.com/GenAI-Hackathon2026/division-a.git
git pull upstream main
git push origin main
```

---

## Rules to remember

> [!IMPORTANT]
> **1. Only touch your own team folder.**
> **2. Open only ONE pull request per team and keep updating it. Do not open a new one for every change.**
> **3. Do not force push, and do not try to delete the `main` branch. These actions are blocked.**
> **4. Use the exact team folder assigned to you.**

---

## Getting help

If you are stuck on any step, contact the organizers do not issue in here.
