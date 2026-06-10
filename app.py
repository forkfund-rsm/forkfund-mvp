import streamlit as st

st.set_page_config(
    page_title="ForkFund MVP",
    page_icon="🍴",
    layout="wide",
)

PAGES = [
    "Home / Concept Overview",
    "Restaurant Onboarding",
    "Credit Passport",
    "Lender Dashboard",
    "Methodology / About",
]


def render_home_page() -> None:
    st.title("ForkFund MVP")
    st.subheader("The Credit Passport for Restaurant Finance")

    st.write(
        """
        ForkFund is a B2B fintech MVP that helps Dutch restaurants become
        finance-ready by turning fragmented restaurant data into a standardised,
        explainable Restaurant Credit Passport.
        """
    )

    st.write(
        """
        The MVP demonstrates the full multi-party flow:
        """
    )

    st.info(
        "Restaurant owner → enters details → connects mock financial data → "
        "receives Credit Passport → lender views dashboard → lender opens the Passport"
    )

    st.markdown("### What this skeleton currently includes")

    st.write(
        """
        This first version only creates the basic Streamlit application structure.
        The next steps will add synthetic data, a rules-based scoring engine,
        the Credit Passport, and the lender dashboard.
        """
    )


def render_restaurant_onboarding_page() -> None:
    st.title("Restaurant Onboarding")

    st.write(
        """
        This page will later allow a restaurant owner to enter business details,
        simulate a KvK lookup, enter a financing request, and connect mock bank,
        POS, and accounting data.
        """
    )

    st.warning("Placeholder page. Functionality will be added in a later step.")


def render_credit_passport_page() -> None:
    st.title("Restaurant Credit Passport")

    st.write(
        """
        This page will later show the generated Restaurant Credit Passport,
        including the score, grade, risk band, restaurant-specific operating
        metrics, peer context, and written risk drivers.
        """
    )

    st.warning("Placeholder page. Functionality will be added in a later step.")


def render_lender_dashboard_page() -> None:
    st.title("Lender Dashboard")

    st.write(
        """
        This page will later show a filterable pool of restaurant profiles.
        Lenders will be able to filter by city, loan amount, loan purpose,
        grade, data completeness, and restaurant-specific risk indicators.
        """
    )

    st.warning("Placeholder page. Functionality will be added in a later step.")


def render_methodology_page() -> None:
    st.title("Methodology / About")

    st.write(
        """
        This page will later explain the rules-based scoring methodology,
        the restaurant-specific metrics, the synthetic-data approach, and the
        MVP boundaries.
        """
    )

    st.markdown("### Deliberately not implemented in this academic MVP")

    st.write(
        """
        - No real PSD2/open-banking connection
        - No live KvK API
        - No live POS/accounting integrations
        - No real lender offers or money movement
        - No iDIN or BKR checks
        - No production-grade security or persistence
        - No predictive default model
        """
    )


def main() -> None:
    st.sidebar.title("ForkFund Navigation")
    selected_page = st.sidebar.radio("Go to", PAGES)

    if selected_page == "Home / Concept Overview":
        render_home_page()
    elif selected_page == "Restaurant Onboarding":
        render_restaurant_onboarding_page()
    elif selected_page == "Credit Passport":
        render_credit_passport_page()
    elif selected_page == "Lender Dashboard":
        render_lender_dashboard_page()
    elif selected_page == "Methodology / About":
        render_methodology_page()


if __name__ == "__main__":
    main()
