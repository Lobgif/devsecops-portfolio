// Messages i18n (fr par défaut, en). Extensible aux langues locales ivoiriennes.
export default defineI18nConfig(() => ({
  legacy: false,
  messages: {
    fr: {
      nav: { home: 'Accueil', forums: 'Forums', login: 'Connexion', signup: 'Inscription' },
      home: { cta: 'Demander' },
    },
    en: {
      nav: { home: 'Home', forums: 'Forums', login: 'Login', signup: 'Sign up' },
      home: { cta: 'Ask' },
    },
  },
}))
