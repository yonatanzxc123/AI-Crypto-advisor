export default function DashboardCard({ title, subtitle, children, actions }) {
  return (
    <section className="dashboard-card">
      <div className="card-heading">
        <div>
          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {actions ? <div className="card-actions">{actions}</div> : null}
      </div>
      <div>{children}</div>
    </section>
  );
}
