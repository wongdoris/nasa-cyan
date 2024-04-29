
import pandas as pd
from sqlalchemy import create_engine, select, func, text
from sqlalchemy.orm import sessionmaker

# Database configuration
db_host = "XXX"
db_user = "admin"
db_password = "XXX"
db_name = "XXX"

# SQLAlchemy engine and session setup
db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def getdata(path=None):
    """
    Extract data from mySQL database
    """
    # Connect to the database
    # db = SessionLocal()

    # # Build the SQL query using text
    # query = text("""
    #     SELECT clat, clon, date, CI_cyano
    #     FROM L3B_CYAN_DAILY
    #     WHERE west >= :lon_from
    #         AND east <= :lon_to
    #         AND south >= :lat_from
    #         AND north <= :lat_to
    # """)

    # # Execute the query with bound parameters
    # result = db.execute(query, {
    #                     "lon_from": lon_from, "lon_to": lon_to, "lat_from": lat_from, "lat_to": lat_to})

    # # Fetch the data into a pandas DataFrame
    # df = pd.DataFrame(result.fetchall(), columns=[
    #                   "clat", "clon", "date", "CI_cyano"])

    # # Close the database connection
    # db.close()

    if path:
        df = pd.read_parquet(path)
    df['date'] = pd.to_datetime(df['date'])

    return df


def data_impute(df: pd.DataFrame):
    """
    Impute dataset with "under detect" value (0.00005)
    """

    # get all locations with CI_cyano >= 0.00005
    locs = df.groupby(['clat', 'clon']).CI_cyano.count().reset_index()
    # get all dates with CI_cyano >= 0.00005
    dates = df.date.unique()

    df_list = [locs[['clat', 'clon']].assign(date=d) for d in dates]
    df_imp = pd.concat(df_list, axis=0)
    df_imp = df_imp.reset_index(drop=True)

    df_imp = pd.merge(df_imp, df[['clat', 'clon', 'date', 'CI_cyano']], how='left', on=[
                      'clat', 'clon', 'date'])
    df_imp['CI_cyano'] = df_imp.CI_cyano.fillna(0.00005)
    df_imp['Year'] = df_imp['date'].dt.year
    df_imp['Month'] = df_imp['date'].dt.month
    df_imp['Day'] = df_imp['date'].dt.day

    return df_imp


def hab_level(df: pd.DataFrame):
    """
    Assign High, Medium, Low HAB levels to CI_cyano values
    """
    HIGH = 0.016
    MED = 0.001

    hab_level = []
    for c in df.CI_cyano.values:
        if c >= HIGH:
            level = 'high'
        elif c >= MED:
            level = 'medium'
        else:
            level = 'low'
        hab_level.append(level)

    df_out = df.copy()
    df_out['HAB'] = hab_level
    df_out['HAB_HIGH'] = (df_out.HAB == 'high')*1
    df_out['HAB_MEDIUM'] = (df_out.HAB == 'medium')*1
    df_out['HAB_HIGH_MED'] = df_out['HAB_HIGH']+df_out['HAB_MEDIUM']

    return df_out
