# Contributing to Thurup

Thank you for your interest in contributing to Thurup! This document provides guidelines and best practices for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)
- [Code Review](#code-review)

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

1. Completed the [Installation Guide](../getting-started/INSTALLATION.md)
2. Read the [Architecture Documentation](./ARCHITECTURE.md)
3. Familiarized yourself with the [Developer Guide](./DEVELOPER_GUIDE.md)

### Setting Up Your Development Environment

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/thurup.git
cd thurup

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/thurup.git

# Install dependencies
cd backend && uv sync
cd ../frontend && npm install
```

---

## Development Workflow

### Branch Strategy

- **`main`**: Stable production code, fully tested features only
- **`play`**: Development branch for iteration and testing
- **Feature branches**: `feature/feature-name` for new features
- **Bug fixes**: `fix/bug-description` for bug fixes

### Creating a Feature Branch

```bash
# Update your local repository
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/my-new-feature
```

### Making Changes

1. **Make small, focused commits**
   - Each commit should represent a single logical change
   - Keep commits atomic and reversible

2. **Write tests first (TDD recommended)**
   - Write failing tests for new features
   - Implement the feature
   - Ensure all tests pass

3. **Run tests frequently**
   ```bash
   # Backend
   cd backend
   uv run pytest -v

   # Frontend
   cd frontend
   npm test
   ```

4. **Keep your branch up to date**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

---

## Code Style Guidelines

### Backend (Python)

#### Formatting

- **Tool**: Black (line length: 100)
- **Linter**: Ruff

```bash
# Format code
uv run black app/ tests/

# Lint code
uv run ruff check app/ tests/

# Auto-fix issues
uv run ruff check --fix app/ tests/
```

#### Style Rules

- Use absolute imports: `from app.game.session import GameSession`
- Type hints for all function signatures
- Docstrings for public functions and classes
- Structured logging with key-value pairs:
  ```python
  logger.info("game_created", game_id=game_id, mode=mode, seats=seats)
  ```

#### Code Organization

- Keep functions small (< 50 lines)
- Single Responsibility Principle
- Use dependency injection
- Async/await for all I/O operations

**Example**:

```python
"""
Module for game session management.
"""

from typing import Optional
from app.models import GameStateDTO
from app.logging_config import get_logger

logger = get_logger(__name__)


async def create_game_session(mode: str, seats: int) -> GameSession:
    """
    Create a new game session.

    Args:
        mode: Game mode ("28" or "56")
        seats: Number of player seats (4 or 6)

    Returns:
        Initialized GameSession instance
    """
    logger.info("creating_game_session", mode=mode, seats=seats)
    session = GameSession(mode=mode, seats=seats)
    return session
```

### Frontend (TypeScript/React)

#### Formatting

- **Tool**: Prettier (configured in `.prettierrc`)
- **Linter**: ESLint

```bash
# Format code
npm run format

# Lint code
npm run lint

# Auto-fix issues
npm run lint:fix
```

#### Style Rules

- Functional components with hooks (no class components)
- Props interfaces for all components
- Destructure props in function signature
- Use TypeScript strict mode (no `any` types)
- Tailwind CSS for styling (avoid inline styles)

**Example**:

```typescript
import { FC } from 'react';
import { Card } from './Card';

interface PlayerHandProps {
  cards: Card[];
  playableCards: Set<string>;
  onCardClick: (cardId: string) => void;
  disabled?: boolean;
}

export const PlayerHand: FC<PlayerHandProps> = ({
  cards,
  playableCards,
  onCardClick,
  disabled = false,
}) => {
  return (
    <div className="flex gap-2 justify-center">
      {cards.map((card) => (
        <PlayingCard
          key={card.id}
          card={card}
          playable={playableCards.has(card.id) && !disabled}
          onClick={() => onCardClick(card.id)}
        />
      ))}
    </div>
  );
};
```

### General Guidelines

- **DRY**: Don't Repeat Yourself
- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It
- **Meaningful names**: Use descriptive variable and function names
- **Comments**: Explain *why*, not *what*

---

## Testing Requirements

### Test Coverage

All contributions must include tests:

- **New features**: Must have unit tests and integration tests
- **Bug fixes**: Must include regression tests
- **Minimum coverage**: 70% for new code

### Running Tests

```bash
# Backend - all tests
cd backend
uv run pytest -v

# Backend - with coverage
uv run pytest --cov=app --cov-report=term-missing

# Frontend - unit tests
cd frontend
npm test

# Frontend - E2E tests (requires backend running)
npm run test:e2e
```

### Test Organization

**Backend**:
- `tests/unit/` - Fast, isolated unit tests
- `tests/integration/` - API integration tests
- `tests/e2e/` - End-to-end tests (requires running server)

**Frontend**:
- `src/**/*.test.tsx` - Component tests
- `tests/e2e/*.spec.ts` - Playwright E2E tests

### Writing Good Tests

```python
# Backend test example
def test_bid_validation():
    """Test that invalid bids are rejected."""
    # Arrange
    session = GameSession(mode="28", seats=4)
    session.start_round()

    # Act
    with pytest.raises(ValueError, match="Bid must be"):
        session.place_bid(seat=0, value=10)  # Below minimum

    # Assert implicitly by exception
```

```typescript
// Frontend test example
describe('Badge', () => {
  it('applies correct variant styles', () => {
    const { rerender } = render(<Badge variant="success">Active</Badge>);

    expect(screen.getByText('Active')).toHaveClass('bg-green-500');

    rerender(<Badge variant="danger">Inactive</Badge>);
    expect(screen.getByText('Inactive')).toHaveClass('bg-red-500');
  });
});
```

---

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Changes to build process or auxiliary tools

### Scope

The scope should specify the place of the commit change:
- `backend`, `frontend`, `docs`, `tests`, `api`, `ui`, `db`, etc.

### Examples

```bash
# Good commit messages
feat(backend): add round history persistence
fix(frontend): resolve WebSocket reconnection race condition
docs: update CONTRIBUTING.md with test guidelines
refactor(api): extract session management to separate module
test(backend): add integration tests for admin endpoints

# Bad commit messages (avoid these)
fix bug
update code
wip
asdfasdf
```

### Subject Line Rules

- Use imperative mood: "add" not "added" or "adds"
- Don't capitalize first letter
- No period at the end
- Limit to 50 characters
- Be specific and descriptive

### Body (Optional)

- Separate from subject with a blank line
- Wrap at 72 characters
- Explain *what* and *why*, not *how*
- Reference issues: `Fixes #123`, `Closes #456`

---

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**
   ```bash
   cd backend && uv run pytest -v
   cd frontend && npm test
   ```

2. **Run code formatters and linters**
   ```bash
   # Backend
   uv run black app/ tests/
   uv run ruff check app/ tests/

   # Frontend
   npm run format
   npm run lint
   ```

3. **Update documentation** if needed

4. **Rebase on latest main**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

### Creating a Pull Request

1. **Push your branch to your fork**
   ```bash
   git push origin feature/my-new-feature
   ```

2. **Create PR on GitHub**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch

3. **Fill out PR template**
   - **Title**: Clear, descriptive summary
   - **Description**:
     - What does this PR do?
     - Why is this change needed?
     - How was it tested?
     - Any breaking changes?
   - **Link related issues**: `Fixes #123`

### PR Title Format

```
<type>(<scope>): <description>
```

Example: `feat(backend): add player statistics endpoint`

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated and passing
- [ ] Dependent changes merged
- [ ] Breaking changes documented

---

## Documentation

### When to Update Documentation

- New features or APIs
- Changed behavior or APIs
- Deprecated features
- New configuration options
- Installation or setup changes

### Documentation Files

- **README.md**: Project overview and quick links
- **docs/getting-started/**: Installation and quickstart guides
- **docs/development/**: Architecture, API reference, developer guide
- **docs/testing/**: Testing guides and strategies
- **docs/planning/**: Roadmap, requirements, technical debt

### Documentation Style

- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Keep documentation close to code (when appropriate)
- Update examples when APIs change

---

## Code Review

### As a Contributor

**Responding to feedback**:
- Be open to constructive criticism
- Ask questions if feedback is unclear
- Make requested changes promptly
- Push additional commits (don't force-push during review)
- Mark conversations as resolved after addressing

**If changes are requested**:
```bash
# Make changes
git add .
git commit -m "refactor: address PR feedback"
git push origin feature/my-new-feature
```

### As a Reviewer

**What to look for**:
- Code correctness and logic
- Test coverage and quality
- Performance implications
- Security considerations
- Code style and readability
- Documentation completeness

**How to provide feedback**:
- Be respectful and constructive
- Explain *why* changes are needed
- Suggest alternatives when possible
- Approve when ready, request changes if needed
- Use GitHub's suggestion feature for small fixes

---

## Additional Guidelines

### Security

- Never commit secrets (API keys, passwords, tokens)
- Use environment variables for configuration
- Validate all user inputs
- Sanitize data before database operations
- Report security vulnerabilities privately

### Performance

- Avoid N+1 queries
- Use async/await for I/O operations
- Minimize bundle size (frontend)
- Lazy load components when appropriate
- Profile before optimizing

### Accessibility

- Use semantic HTML elements
- Include ARIA labels where needed
- Ensure keyboard navigation works
- Test with screen readers
- Maintain color contrast ratios

---

## Getting Help

- **Documentation**: Check [docs/README.md](../README.md)
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Tag maintainers for review help

---

## License

By contributing to Thurup, you agree that your contributions will be licensed under the project's license.

---

**Thank you for contributing to Thurup! 🎉**
